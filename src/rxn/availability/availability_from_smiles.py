from typing import Callable, Iterable, Iterator, Optional

from .smiles_availability import AvailabilityMatch, SmilesAvailability


class AvailabilityFromSmiles(SmilesAvailability):
    """
    Query availability of SMILES strings from exact matches.
    """

    def __init__(
        self,
        compounds: Iterable[str],
        standardizer: Optional[Callable[[str], str]] = None,
    ):
        super().__init__(standardizer=standardizer)

        self.available_compounds = set(compounds)

    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """See base class for documentation."""
        if smiles in self.available_compounds:
            yield AvailabilityMatch(details=f'Matching exact SMILES, "{smiles}".')
