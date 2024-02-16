from typing import Callable, Iterator, Optional, Union

from .databases import DB
from .smiles_availability import AvailabilityMatch, SmilesAvailability


class AvailabilityFromDatabase(SmilesAvailability):
    """
    Query availability of SMILES strings from an instance of DB (such as MongoDB).
    """

    def __init__(
        self,
        database: DB,
        standardizer: Optional[Callable[[str], str]] = None,
        pricing_threshold: Union[int, float] = 0,
    ):
        super().__init__(standardizer=standardizer)

        self.database = database

        # NOTE: the database classes expect an integer
        self.pricing_threshold = int(pricing_threshold)

    def _find_matches(self, smiles: str) -> Iterator[AvailabilityMatch]:
        """See base class for documentation."""
        if self.database.availability(
            smi=smiles, pricing_threshold=self.pricing_threshold
        ):
            yield AvailabilityMatch(details="Found in the database.")
