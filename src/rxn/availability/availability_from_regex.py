from typing import Callable, Iterable, Iterator, Optional, Pattern

from .smiles_availability import AvailabilityMatch, SmilesAvailability


class AvailabilityFromRegex(SmilesAvailability):
    """
    Query availability of SMILES strings from regex checks.
    """

    def __init__(
        self,
        regexes: Iterable[Pattern],
        standardizer: Optional[Callable[[str], str]] = None,
    ):
        super().__init__(standardizer=standardizer)

        self.available_regexes = list(regexes)

    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """See base class for documentation."""
        for pattern in self.available_regexes:
            if pattern.search(smiles):
                yield AvailabilityMatch(f'Matching regex "{pattern.pattern}".')
