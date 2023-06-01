# Generalized Glossing Guidelines

This repository contains tools for the Generalized Glossing Guidelines (GGG or G3). GGG is a way of representing interlinear glossed text so that non-concatenative processes are given the same status as affixation.

Currently, there are two Python files in the repository: one for validating GGG YAML files and the other for converting GGG representations into a BILOU linearization.

## Validation

The script `validate_ggg.py` takes as input GGG YAML or a batch consisting of all the YAML files in a directory and succeeds if they are valid.

This will validate the GGG file `akkadian.yml`:
```
python validate_ggg.py -i akkadian.yml
```

And this will validate all of the GGG files in the currently directory (assuming that all `*.yml` files are GGG)
```
python validate_ggg.py -b
```

## Parsing and Conversion to BILOU Representation

The library `ggg2bilou.py` implements the parsing of the `ur` and `gl` files of a GGG file and converts them to a BILOU linearization suitable for consumption or generation by a sequence model.