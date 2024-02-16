# rxn-availability

## Development setup

```console
pip install -e ".[dev,rdkit]"
```

## Example

The easiest way to use the package is to rely on the `IsAvailable` object:

```python
from rxn.availability import IsAvailable

is_available_object = IsAvailable()
smiles = "B1C2CCCC1CCC2"
print(f"{smiles} availability: {is_available_object(smiles}")

# BYOC: bring your own compounds
compounds_filepath = "tests/example_compounds.txt"
is_available_object = IsAvailable(additional_compounds_filepath=compounds_filepath)
smiles = "CC(Cc1ccc(cc1)C(C(=O)O)C)C"
print(f"{smiles} availability: {is_available_object(smiles}")
```
