from pathlib import Path

from rxn.availability import IsAvailable

compounds_filepath = Path(__file__).parent / "example_compounds.txt"


def test_is_available_object():
    is_available_object = IsAvailable()
    assert is_available_object("B1C2CCCC1CCC2")
    assert not is_available_object("CC(Cc1ccc(cc1)C(C(=O)O)C)C")

    is_available_object = IsAvailable(additional_compounds_filepath=compounds_filepath)
    assert is_available_object("B1C2CCCC1CCC2")
    assert is_available_object("CC(Cc1ccc(cc1)C(C(=O)O)C)C")
    assert not is_available_object("C1=CC=C2C(=C1)C=CC=NN2")
