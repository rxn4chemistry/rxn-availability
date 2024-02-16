import logging
from typing import Callable, Iterable, Iterator, Optional

from .smiles_availability import AvailabilityMatch, SmilesAvailability

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AvailabilityCombiner(SmilesAvailability):
    """
    Query the availability of SMILES strings by combining multiple other classes.

    This class is useful when the availability of SMILES strings is provided
    by multiple components - for instance, it avoids calling the standardization
    multiple times.
    """

    def __init__(
        self,
        sources: Iterable[SmilesAvailability],
        add_source_to_match_info_key: Optional[str] = None,
        excluded_sources: Optional[Iterable[Callable[[str], bool]]] = None,
        standardizer: Optional[Callable[[str], str]] = None,
    ):
        """
        Args:
            sources: instances of SmilesAvailability for the available sources.
            add_source_to_match_info_key: if specified, a pointer to the source will
                be added to the AvailabilityMatch info dictionary under that key.
            excluded_sources: sources to exclude, either given as an instance of
                SmilesAvailability, or as a callable function.
            standardizer: see doc in base class.
        """
        super().__init__(standardizer=standardizer)
        self.sources = list(sources)
        self.add_source_to_match_info_key = add_source_to_match_info_key
        self.excluded_sources = (
            [] if excluded_sources is None else list(excluded_sources)
        )

    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """See base class for documentation."""

        # Note: when it gets there, the SMILES string has already been
        # standardized (in the base class).

        if any(excluded(smiles) for excluded in self.excluded_sources):
            logger.debug(f'SMILES "{smiles}" is unavailable due to exclusion rule.')
            return

        for source in self.sources:
            for match in source.find_matches(smiles):
                if self.add_source_to_match_info_key is not None:
                    match.info[self.add_source_to_match_info_key] = source
                yield match
