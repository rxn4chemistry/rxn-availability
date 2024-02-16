import re
from pathlib import Path
from typing import List, Pattern, Set

import importlib_resources


def default_available_regexes() -> List[Pattern]:
    """Get regex patterns for always available compounds.

    Returns:
        a list of regex patterns.
    """
    return [
        # Get all ions
        re.compile(r"^\[\w{1,3}[+-]\d?\]$"),
        # Get Single and double elements (e.g: O2)
        re.compile(r"^([A-Z][a-z]?){1,2}$"),
        # Get Single and double elements in squared parentheses
        re.compile(r"^(\[[A-Z][a-z]?\]){1,2}$"),
        # Matches stuff like [HH], [BrBr]
        re.compile(r"^\[([A-Z][a-z]?){1,2}\]$"),
        re.compile(r"^[A-Z].?[A-Z]$"),
    ]


def default_available_smarts_patterns() -> List[str]:
    """Get SMARTS patterns for always available compounds.

    Returns:
        a list of SMARTS.
    """
    # NOTE: biochemical reaction cofactors
    return [
        "O=C(NCC*)CCNC(=O)C(O)C(C)(C)COP(=O)(*)OP(=O)(*)OC*3O*(n2cnc1c(ncnc12)N)*(O)*3OP(=O)(*)*",
        "**1*(*)*(COP(*)(=O)OP(*)(=O)OC*2O*(*)*(*)*2*)O*1*",
        "**1*(*)*(O*1COP(*)(=O)O)[R]",
        "*P(*)(=O)O*1*(*)*(*)O[*]1COP(*)(*)=O",
        "**1*(*)*(O*1CS*)[R]",
        "**1**2**3*(**(=O)**3=O)*(*)*2**1*",
        "*~1~*~*~2~*~*~1~*~*~1~*~*~*(~*~*~3~*~*~*(~*~*~4~*~*~*(~*~2)~*~4)~*~3)~*~1",
        "S1[Fe]S[Fe]1",
    ]


def common_biochemical_byproducts() -> Set[str]:
    """Get common biochemical compounds that are not part of a commercial compound database.

    Returns:
        a set of SMILES.
    """
    return {
        "O=P([O-])([O-])[O-]",
        "O=P([O-])([O-])O",
        "C[N+](C)(C)CCO",
        "NCCO",
        "O=P([O-])([O-])OP(=O)([O-])[O-]",
        "O=P([O-])([O-])OP(=O)([O-])O",
        "O=C([O-])CCC(=O)C(=O)[O-]",
        "CC(=O)[O-]",
        "CC(=O)C(=O)[O-]",
    }


def default_available_compounds() -> Set[str]:
    """Get common available compounds that are not part of a commercial compound database.

    Returns:
        a set of SMILES.
    """
    return _get_compounds_from_packaged_file("common_compounds.txt")


def _get_compounds_from_packaged_file(packaged_file_name: str) -> Set[str]:
    """Get the compounds contained in a file that is packaged with rxn-availability.

    Args:
        packaged_file_name: file containing one SMILES per line, and potentially
            some lines for comments (starting with "#"). This file must be listed
            in setup.cfg!

    Returns:
        a set of SMILES.
    """
    return get_compounds_from_file(
        importlib_resources.files(__package__) / "resources" / packaged_file_name
    )


def get_compounds_from_file(file_path: Path) -> Set[str]:
    """Get the compounds from file.

    Args:
        file_path: file containing one SMILES per line, and potentially
            some lines for comments (starting with "#").

    Returns:
        a set of SMILES.
    """
    with open(file_path) as fp:
        raw_text: str = fp.read()
    return {line for line in raw_text.splitlines() if not line.startswith("#")}
