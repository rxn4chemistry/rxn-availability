import re

from rxn.chemutils.conversion import canonicalize_smiles

from rxn.availability.availability_from_regex import AvailabilityFromRegex


def test_availability_from_regex():
    regexes = [
        re.compile(re.escape("[Na+]")),  # sodium ion
        re.compile(re.escape("CCc2cc")),  # random piece of SMILES
    ]

    availability_from_regex = AvailabilityFromRegex(regexes=regexes)

    # Basic checks
    assert availability_from_regex("CCc2ccccc2")
    assert availability_from_regex("[Na+].[Cl-]")
    assert not availability_from_regex("[Na]CCC")

    # possible to have several matches
    assert len(list(availability_from_regex.find_matches("[Na+].CCCCc2ccccc2CC"))) == 2

    # If a standardizer is given: will standardize before trying to match.
    # In the case below, no match anymore because the number will be 1 after canonicalization.
    availability_from_regex.standardizer = canonicalize_smiles
    assert not availability_from_regex("CCc2ccccc2")
