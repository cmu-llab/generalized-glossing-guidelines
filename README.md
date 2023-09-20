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
```bash
python validate_ggg.py -b
```

## Parsing and Conversion to BILOU Representation

The library `ggg2bilou.py` implements the parsing of the `ur` and `gl` files of a GGG file and converts them to a BILOU linearization suitable for consumption or generation by a sequence model.

```python
> import ggg2bilou
> ggg2bilou.merged_form_gloss("f{oo>ee}t", "foot{PL}")
[Character(char='f', tag='B', op='S', span=0, gloss='foot'), Character(char='o', tag='I', op='D', span=0, gloss='foot'), Character(char='o', tag='I', op='D', span=0, gloss='foot'), Character(char='e', tag='B', op='A', span=1, gloss='PL'), Character(char='e', tag='L', op='A', span=1, gloss='PL'), Character(char='t', tag='L', op='S', span=0, gloss='foot')]
```

## Citation

```
@inproceedings{mortensen-etal-2023-generalized,
    title = "Generalized Glossing Guidelines: An Explicit, Human- and Machine-Readable, Item-and-Process Convention for Morphological Annotation",
    author = "Mortensen, David R.  and
      Gulsen, Ela  and
      He, Taiqi  and
      Robinson, Nathaniel  and
      Amith, Jonathan  and
      Tjuatja, Lindia  and
      Levin, Lori",
    booktitle = "Proceedings of the 20th SIGMORPHON workshop on Computational Research in Phonetics, Phonology, and Morphology",
    month = jul,
    year = "2023",
    address = "Toronto, Canada",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.sigmorphon-1.7",
    doi = "10.18653/v1/2023.sigmorphon-1.7",
    pages = "58--67",
    abstract = "Interlinear glossing provides a vital type of morphosyntactic annotation, both for linguists and language revitalists, and numerous conventions exist for representing it formally and computationally. Some of these formats are human readable; others are machine readable. Some are easy to edit with general-purpose tools. Few represent non-concatentative processes like infixation, reduplication, mutation, truncation, and tonal overwriting in a consistent and formally rigorous way (on par with affixation). We propose an annotation convention{\^a}€{''}Generalized Glossing Guidelines (GGG) that combines all of these positive properties using an Item-and-Process (IP) framework. We describe the format, demonstrate its linguistic adequacy, and compare it with two other interlinear glossed text annotation schemes.",
}
```
