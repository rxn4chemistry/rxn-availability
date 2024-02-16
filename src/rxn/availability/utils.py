from typing import Callable


def wrap_standardizer_with_tilde_substitution(
    smiles_standardizer: Callable[[str], str]
) -> Callable[[str], str]:
    """
    Wrap a SMILES standardizer to make it replace tildes with dots.

    Since IsAvailable is still being used with molecules containing "~" as a
    fragment bond, it is necessary to remain compatible with it. This function
    ensures this compatibility by replacing tildes with dots as a first step
    for the SMILES standardization.
    """

    def wrapped_standardizer(smiles: str) -> str:
        smiles = smiles.replace("~", ".")
        return smiles_standardizer(smiles)

    return wrapped_standardizer
