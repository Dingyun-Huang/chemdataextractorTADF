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

Usage
------------

An example run can be found in `example_extraction.ipynb`, where you should put the documents (Elsevier XMLs and RSC HTMLs) in the `papers_for_extraction` folder.
The notebook does not save the extracted by default, but you can do so with `json.dumps`.

The helper functions for data cleaning and post-processing are given in `data_cleaning_utils.ipynb`. You can copy the functions that you would like to use into your scripts.

An example of converting IUPAC names into SMILES is given in `iupac_to_smiles.ipynb`. You need to change the path of the `.jar` file to the actual path in your computer.

