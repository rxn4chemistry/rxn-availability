from typing import Callable, Iterable, Iterator, Optional

from rdkit.Chem import MolFromSmarts, MolFromSmiles

from .smiles_availability import AvailabilityMatch, SmilesAvailability


class AvailabilityFromSmarts(SmilesAvailability):
    """
    Query availability of SMILES strings from SMARTS matching.
    """

    def __init__(
        self,
        smarts: Iterable[str],
        standardizer: Optional[Callable[[str], str]] = None,
    ):
        super().__init__(standardizer=standardizer)

        self.available_smarts = [(MolFromSmarts(s), s) for s in smarts]

    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """See base class for documentation."""
        molecule = MolFromSmiles(smiles)
        if not molecule:
            return

        for pattern, smarts in self.available_smarts:
            if molecule.HasSubstructMatch(pattern):
                yield AvailabilityMatch(details=f'Matching SMARTS "{smarts}".')
