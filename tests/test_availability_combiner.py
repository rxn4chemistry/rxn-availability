from typing import Callable, List

from rxn.availability.availability_combiner import AvailabilityCombiner
from rxn.availability.availability_from_smarts import AvailabilityFromSmarts
from rxn.availability.availability_from_smiles import AvailabilityFromSmiles


def test_availability_combiner():
    # exclusion criteria (note that simple callables are allowed)
    excluded: List[Callable[[str], bool]] = [
        AvailabilityFromSmiles(["CO", "COC"]),
        AvailabilityFromSmarts(["[Na+]"]),
        lambda x: x == "C",
    ]

    exact_smiles_availability = AvailabilityFromSmiles(["CCCC", "C", "CO", "CCO"])
    smarts_availability = AvailabilityFromSmarts(["[O;H1]"])  # simple hydroxy oxygen

    combined = AvailabilityCombiner(
        sources=[exact_smiles_availability, smarts_availability],
        excluded_sources=excluded,
    )

    # simple positive checks
    assert combined.is_available("CCCCCCO")
    assert combined.is_available("CCCC")
    assert not combined.is_available("CCC")

    # exclusion takes precedence over availability
    assert not combined.is_available("CO")
    assert not combined.is_available("C")

    # getting the information on which class the availability comes from
    combined.add_source_to_match_info_key = "dummy_key"
    matches = list(combined.find_matches("CCO"))
    assert len(matches) == 2
    assert matches[0].info["dummy_key"] is exact_smiles_availability
    assert matches[1].info["dummy_key"] is smarts_availability
