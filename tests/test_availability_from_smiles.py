from rxn.chemutils.conversion import canonicalize_smiles

from rxn.availability.availability_from_smiles import AvailabilityFromSmiles


def test_availability_from_smiles():
    available = ["CCO", "CCCC"]

    availability_from_smiles = AvailabilityFromSmiles(
        compounds=available, standardizer=canonicalize_smiles
    )

    assert availability_from_smiles("CCO")
    assert availability_from_smiles("CCCC")
    assert not availability_from_smiles("C")

    # invalid SMILES are not available
    assert not availability_from_smiles("invalid")

    # non-canonical form is found, except if we remove the standardizer
    assert availability_from_smiles("OCC")
    availability_from_smiles.standardizer = None
    assert not availability_from_smiles("OCC")
