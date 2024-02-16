import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterator, Optional

from attr import Factory, define

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@define
class AvailabilityMatch:
    """
    Class holding the information about a match when querying the availability
    of a SMILES string.

    Attributes:
        details: details on the match.
        info: to hold any additional information related to the available
            compound, such as price, ID, etc.
    """

    details: str
    info: Dict[str, Any] = Factory(dict)


class SmilesAvailability(ABC):
    """
    Base class for the availability of SMILES strings.

    The base class provides the public functions is_available(), first_match(), and
    find_matches(), which are to be called by users. For derived classes, it is
    sufficient to implement the protected function _find_matches().
    """

    def __init__(self, standardizer: Optional[Callable[[str], str]] = None):
        """
        Args:
            standardizer: function to call for standardizing SMILES strings
                before the availability check (typically: canonicalization).
                Defaults to no modification of the SMILES strings.
        """
        self.standardizer = standardizer

    def __call__(self, smiles: str) -> bool:
        """
        Whether the given SMILES string is available.

        This makes the object callable; equivalent to calling is_available().
        """
        return self.is_available(smiles)

    def is_available(self, smiles: str) -> bool:
        """Whether the given SMILES string is available."""

        # We use any() so that the function stops as soon as a source is
        # obtained. This avoids iterating to the end unnecessarily.
        return any(True for _ in self.find_matches(smiles))

    def first_match(self, smiles: str) -> Optional[AvailabilityMatch]:
        """Get the first source match for the given SMILES string (None if no
        match at all)."""

        # Note: this stops as soon as the first match is found.
        return next(self.find_matches(smiles), None)

    def find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """
        Find the sources from where a SMILES string is available.

        The formulation of the function as a generator/iterator allows for early
        stopping when a first source is found.

        Args:
            smiles: SMILES string to get the availability for.

        Returns:
            Iterator/Generator over matches for the given SMILES string.
        """

        if self.standardizer is not None:
            try:
                smiles = self.standardizer(smiles)
            except Exception as e:
                logger.warning(f'Error when standardizing SMILES "{smiles}": {e}')
                return

        yield from self._find_matches(smiles)

    @abstractmethod
    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """
        Protected function to obtain the matches for a given SMILES string.

        This function is called from the public find_matches() function, on an
        already standardized SMILES string.

        Args:
            smiles: SMILES string to get the sources for (already standardized).
        """
