ChemDataExtractor TADF
==================================

__ChemDataExtractor TADF__ is an adaption of __ChemDataExtractor__ v2, which is a toolkit for extracting chemical information from the scientific literature. The adaption was made for text-mining the thermally-activated delayed fluorescence (TADF) domain.


Prerequisites
------------

- __git__: Install `git` for downloading the package https://git-scm.com/book/en/v2/Getting-Started-Installing-Git.
- __conda__: Dependency manager used to create Python virtual environments https://conda.io/projects/conda/en/latest/user-guide/install/index.html.

Installation
------------

Download and go to the directory of the repository.
```
git clone https://github.com/Dingyun-Huang/chemdataextractorTADF.git
cd chemdataextractorTADF
```

Create and activate a new Python 3.7 environment.
```
conda create --name cde_tadf python=3.7
```

When you are in the repository directory, install ChemDataExtractor and tadf_models.
```
pip install -e .
pip install -e tadf_models
cde data download
```

Run all tests to ensure correct installation.
```
python -m pytest -W ignore::DeprecationWarning
```

Features
--------

- HTML, XML and PDF document readers
- Chemistry-aware natural language processing pipeline
- Chemical named entity recognition
- Rule-based parsing grammars for property and spectra extraction
- Table parser for extracting tabulated data
- Document processing to resolve data interdependencies

Documentation & Development
-----------------------------

Please read the documentation for instructions on contributing to the project.

https://cambridgemolecularengineering-chemdataextractor-development.readthedocs-hosted.com/en/latest/

License
-------

ChemDataExtractor v2 is licensed under the `MIT license`_, a permissive, business-friendly license for open source
software.

MIT license: https://github.com/CambridgeMolecularEngineering/ChemDataExtractor/blob/master/LICENSE
