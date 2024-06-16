ChemDataExtractor TADF
==================================

__ChemDataExtractor TADF__ is an adaption of __ChemDataExtractor__ v2, which is a toolkit for extracting chemical information from the scientific literature. The adaption was made for text-mining the thermally-activated delayed fluorescence (TADF) domain.

Prerequisites
------------

- __git__: Install `git` for downloading the package https://git-scm.com/book/en/v2/Getting-Started-Installing-Git.
- __conda__: Dependency manager used to create Python virtual environments https://conda.io/projects/conda/en/latest/user-guide/install/index.html.

Installation
------------

### Link to BiliBili video How to Install CDE from scratch [here](https://www.bilibili.com/video/BV18TV8eoEuK/?share_source=copy_web&vd_source=f28b2a599b5466304d1f1ed147937fe8).

Download and go to the directory of the repository.
```
git clone https://github.com/Dingyun-Huang/chemdataextractorTADF.git
cd chemdataextractorTADF
```

Create and activate a new Python 3.7 environment.
```
conda create --name cde_tadf python=3.7
conda activate cde_tadf
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
The notebook does not save the extracted records by default, but you can do so with `json.dumps`.

The helper functions for data cleaning and post-processing are given in `data_cleaning_utils.ipynb`. You can copy the functions that you would like to use into your scripts.

An example of converting IUPAC names into SMILES is given in `iupac_to_smiles.ipynb`. You need to change the path of the `opsin_cli.jar` file to the actual path in your computer.

Citing
------------

If you use the database or **chemdataextractorTADF** in your work, please cite the following works:

Huang, D., Cole, J.M. A database of thermally activated delayed fluorescent molecules auto-generated from scientific literature with ChemDataExtractor. Sci Data 11, 80 (2024). https://doi.org/10.1038/s41597-023-02897-3

Huang, D. & Cole, J. M. A Database of Thermally Activated Delayed Fluorescent Molecules Auto-generated from Scientific Literature with ChemDataExtractor. (2023) https://doi.org/10.6084/m9.figshare.24004182.

Mavračić, J., Court, C. J., Isazawa, T., Elliott, S. R. & Cole, J. M. ChemDataExtractor 2.0: Autopopulated Ontologies for Materials Science. J. Chem. Inf. Model. 61, 4280–4289 (2021). https://doi.org/acs.jcim.1c00446

Funding
------------

This project was financially supported by the [Science and Technology Facilities Council (STFC)](https://stfc.ukri.org/) and the [Royal Academy of Engineering](https://www.raeng.org.uk/) (RCSRF1819\7\10). Dingyun Huang recieves his PhD scholarship from the Cambridge Commonwealth, European and International Trust and the China Scholarship Council for a PhD scholarship.
