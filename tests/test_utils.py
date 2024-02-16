from rxn.chemutils.conversion import canonicalize_smiles

from rxn.availability.utils import wrap_standardizer_with_tilde_substitution


def test_wrap_standardizer_with_tilde_substitution():
    standardizer = canonicalize_smiles
    wrapped_standardizer = wrap_standardizer_with_tilde_substitution(standardizer)

    # If no tilde in the SMILES: both give the same result.
    for smiles in ["C(C)O", "C(C).OC", "O.C.N"]:
        assert wrapped_standardizer(smiles) == standardizer(smiles)

    # When a tilde is present, only the wrapped standardizer converts it to a dot.
    assert standardizer("C~O") == "C~O"
    assert wrapped_standardizer("C~O") == "C.O"

    # In cases where the tilde leads to a failed canonicalization, only the
    # wrapped standardizer works.
    assert wrapped_standardizer("[Na+]~[H-]") == "[H-].[Na+]"
    assert standardizer("[Na+]~[H-]") == "[NaH+]"
