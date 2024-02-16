import logging
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set, Union

from rxn.chemutils.smiles_standardization import standardize_molecules

from .availability_combiner import AvailabilityCombiner
from .availability_from_database import AvailabilityFromDatabase
from .availability_from_regex import AvailabilityFromRegex
from .availability_from_smarts import AvailabilityFromSmarts
from .availability_from_smiles import AvailabilityFromSmiles
from .databases import initialize_databases_from_environment_variables
from .defaults import (
    common_biochemical_byproducts,
    default_available_compounds,
    default_available_regexes,
    default_available_smarts_patterns,
    get_compounds_from_file,
)
from .smiles_availability import AvailabilityMatch, SmilesAvailability
from .utils import wrap_standardizer_with_tilde_substitution

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

AVAILABILITY_METADATA = OrderedDict(
    [
        (
            "common",
            {"color": "#002d9c", "label": "Common molecule available by default"},
        ),
        (
            "model",
            {
                "color": "#0f62fe",
                "label": "Molecule available using a model-specific database",
            },
        ),
        (
            "emolecules",
            {
                "color": "#28a30d",
                "label": "Molecule commercially available on eMolecules.com",
            },
        ),
        (
            "database",
            {
                "color": "#3ddbd9",
                "label": "Molecule commercially available from a database",
            },
        ),
        (
            "unavailable",
            {"color": "#ce4e04", "label": "Not able to find a synthetic path"},
        ),
        ("from_file", {"color": "#f1c21b", "label": "Molecule from file"}),
    ]
)


def default_standardize_molecules(smiles: str) -> str:
    """Standardize molecules.

    Args:
        smiles (str): standardize molecules with defaults.

    Returns:
        standardized molecules.
    """
    return standardize_molecules(
        smiles,
        canonicalize=True,
        sanitize=True,
        inchify=False,
        fragment_bond="~",
        ordered_precursors=True,
        molecule_token_delimiter=None,
        is_enzymatic=False,
        enzyme_separator="|",
    )


class IsAvailable:
    """
    Class handling the availability of compounds.

    Combines different sources for availability and exclusion, mixing default
    (hard-coded) values, availability databases, and user-provided input.
    """

    def __init__(
        self,
        pricing_threshold: int = 0,
        always_available: Optional[List[str]] = None,
        model_available: Optional[Iterable[str]] = None,
        excluded: Optional[List[str]] = None,
        avoid_substructure: Optional[List[str]] = None,
        are_materials_exclusive: bool = False,
        standardization_function: Callable[[str], str] = default_standardize_molecules,
        additional_compounds_filepath: Optional[Union[Path, str]] = None,
    ) -> None:
        """
        Initialize the availability probing object.

        Args:
            always_available: list of always available compounds.
            model_available: compounds available for the selected model.
            excluded: excluded compounds.
            avoid_substructure: substructures to avoid.
            are_materials_exclusive: flag indicating whether the materials
                provided by users are replacing (True) or complementing (False) the available
                compounds associated to a model and the ones from the availability database.
                Defaults to False, a.k.a., complementing the list.
            standardization_function: function to standardize a SMILES string.
                It handles multiple molecule separated with '.' as well as '~' fragment bonds.
            additional_compounds_filepath: path to compounds to add to the available ones
                from a custom file source.
        """
        self.standardization_function = wrap_standardizer_with_tilde_substitution(
            standardization_function
        )
        self.are_materials_exclusive = are_materials_exclusive

        additional_compounds_from_filepath: Set[str] = set()
        if additional_compounds_filepath is not None:
            additional_compounds_from_filepath = {
                standardization_function(smiles)
                for smiles in get_compounds_from_file(
                    Path(additional_compounds_filepath)
                )
            }

        # Compounds available by default
        self.from_default_compounds = AvailabilityFromSmiles(
            default_available_compounds()
            | common_biochemical_byproducts()
            | additional_compounds_from_filepath
        )
        self.from_default_regexes = AvailabilityFromRegex(default_available_regexes())
        self.from_default_smarts = AvailabilityFromSmarts(
            default_available_smarts_patterns()
        )

        # User and model available compounds
        self.from_user = AvailabilityFromSmiles(self._ensure_iterable(always_available))
        self.from_model = AvailabilityFromSmiles(self._ensure_iterable(model_available))

        # Database compounds
        self._pricing_threshold = pricing_threshold
        self.from_database = {
            database_name: AvailabilityFromDatabase(
                database, pricing_threshold=self._pricing_threshold
            )
            for database_name, database in initialize_databases_from_environment_variables().items()
        }

        # Excluded compounds
        self.excluded_compounds = AvailabilityFromSmiles(
            self._ensure_iterable(excluded)
        )
        self.excluded_substructures = AvailabilityFromSmarts(
            self._ensure_iterable(avoid_substructure)
        )

        # Under which key the instance of SmilesAvailability will be stored in the
        # 'info' dict of AvailabilityMatch.
        self.key_for_source_instance = "smilesavailability_instance"

    def _ensure_iterable(
        self, optional_iterable: Optional[Iterable[str]]
    ) -> Iterable[str]:
        """For optional iterables, replace the None value by an empty list."""
        if optional_iterable is None:
            return []
        return optional_iterable

    def __call__(self, smiles: str) -> bool:
        """
        Inquire the availability of a SMILES string.

        Args:
            smiles: SMILES string for which the availability is needed.

        Returns:
            False if the SMILES string is not available, True otherwise.
        """
        first_match = self._get_first_availability_match(smiles)
        if first_match is None:
            logger.debug(f'SMILES "{smiles}" is not available.')
            return False

        logger.debug(f'SMILES "{smiles}" is available: {first_match.details}.')
        return True

    def get_availability_metadata(self, smiles: str) -> Dict:
        """Get availability metadata given a SMILES string.

        Args:
            smiles: SMILES string for which the availability metadata are needed.

        Returns:
            metadata on availability.
        """

        match = self._get_first_availability_match(smiles)
        if match is None:
            availability_metadata_key = "unavailable"
        else:
            source = match.info[self.key_for_source_instance]
            availability_metadata_key = self._source_to_category(source)

        return AVAILABILITY_METADATA[availability_metadata_key]

    def is_expandable(self, smiles: str) -> bool:
        """
        Get expandability given a SMILES.

        Args:
            smiles: SMILES string for which the expandable information is needed.

        Returns:
            whether the molecule is expandable.
        """

        # Note: this does the same thing as the original implementation - maybe,
        # it will be necessary to review this behavior at some point. For instance,
        # it does not consider the default SMARTS strings.
        sources = [
            self.from_default_compounds,
            self.from_default_regexes,
            self.from_user,
        ]
        match = self._get_first_availability_match(
            smiles, sources=sources, excluded_sources=[]
        )

        # if there is no match, it means that the molecule is expandable.
        return match is None

    def _get_first_availability_match(
        self,
        smiles: str,
        sources: Optional[Iterable[SmilesAvailability]] = None,
        excluded_sources: Optional[Iterable[SmilesAvailability]] = None,
    ) -> Optional[AvailabilityMatch]:
        """
        Get the first availability match (None if nothing found).

        Args:
            sources: availability sources to consider. Defaults to all the sources
                to consider in this class (default compounds, user compounds,
                database, etc.).
            excluded_sources: sources to exclude. Defaults to the excluded compounds
                and substructures.
        """
        if sources is None:
            sources = [
                self.from_default_compounds,
                self.from_default_regexes,
                self.from_default_smarts,
                self.from_user,
            ]
            if not self.are_materials_exclusive:
                sources.append(self.from_model)
                sources.extend(self.from_database.values())
        if excluded_sources is None:
            excluded_sources = [
                self.excluded_compounds,
                self.excluded_substructures,
            ]

        availability_combiner = AvailabilityCombiner(
            sources=sources,
            add_source_to_match_info_key=self.key_for_source_instance,
            excluded_sources=excluded_sources,
            standardizer=self.standardization_function,
        )

        return availability_combiner.first_match(smiles)

    def _source_to_category(self, source: SmilesAvailability) -> str:
        """
        Get the category corresponding to a SmilesAvailability instance.

        Corresponds to the key being used in AVAILABILITY_METADATA.
        """
        if any(
            source is s
            for s in [
                self.from_default_compounds,
                self.from_default_regexes,
                self.from_default_smarts,
                self.from_user,
            ]
        ):
            return "common"

        if source is self.from_model:
            return "model"

        for key, value in self.from_database.items():
            if source is value:
                return key if key == "emolecules" else "database"

        raise ValueError(f'Cannot get category for source "{source}"')

    @property
    def pricing_threshold(self) -> int:
        """
        Returns the current value of this object's pricing threshold (USD per g/L).
        """
        return self._pricing_threshold

    @pricing_threshold.setter
    def pricing_threshold(self, value: int):
        """
        Sets the value of this object's pricing threshold to the given value (in USD per g/L)
        """
        self._pricing_threshold = value
        for database in self.from_database.values():
            database.pricing_threshold = self._pricing_threshold
