from rxn.availability.availability_from_smarts import AvailabilityFromSmarts


def test_is_available_from_smarts():
    # 2-connected (etheric) oxygen next to a carbon atom, or a halogen atom
    smarts = ["[O;D2]C", "[F,Cl,Br,I]"]
    availability_from_smarts = AvailabilityFromSmarts(smarts=smarts)

    # Matching one of the two rules
    assert availability_from_smarts("COC")
    assert availability_from_smarts("OCCBr")
    assert availability_from_smarts("F")
    assert availability_from_smarts("CF")
    assert availability_from_smarts("C1COCC1")

    # Not matching
    assert not availability_from_smarts("CCO")
    assert not availability_from_smarts("NON")
    assert not availability_from_smarts("OCCS")

    # invalid SMILES are not available
    assert not availability_from_smarts("invalid")


def test_availability_matches_from_smarts():
    # 2-connected (etheric) oxygen next to a carbon atom, or a halogen atom
    smarts = ["[O;D2]C", "[F,Cl,Br,I]"]
    availability_from_smarts = AvailabilityFromSmarts(smarts=smarts)

    # The class allows multiple matches for the different SMARTS
    assert len(list(availability_from_smarts.find_matches("COC"))) == 1
    assert len(list(availability_from_smarts.find_matches("COCCCBr"))) == 2
    assert len(list(availability_from_smarts.find_matches("CCO"))) == 0

    # look into the details strings
    matches = list(availability_from_smarts.find_matches("COCCCBr"))
    details_strings = [match.details for match in matches]
    assert details_strings == [
        'Matching SMARTS "[O;D2]C".',
        'Matching SMARTS "[F,Cl,Br,I]".',
    ]
