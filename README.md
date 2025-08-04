# InPreD bioinformatics pipelineREADME

&nbsp;

In this repository you will find a detailed explanation of all the steps required to run the InPreD bioinformatics pipeline, this includes the followings points:

&nbsp;

  - Importing metadata to *TSD* server
  - Preparing conditions to launch the pipeline
  - Running the pipeline step-by-step
  - E-mail drafts to be sent to the InPreD team
  - Q & A section
  - Check list to be used in each sequencing run

&nbsp;

The *README* file is written in [*Rmarkdown (.Rmd)*](https://rmarkdown.rstudio.com/lesson-1.html), therefore we need to render it to create the **interactive html README file**.
We assume the user has acces to and is familiar with [*R studio*](https://posit.co/download/rstudio-desktop/).

&nbsp;


## Create interactive html README

&nbsp;

### 1. Download this repository

```
git clone https://github.com/jaimicore/InPreD_README.git
cd InPreD_README
```



# To be continued ...


### 2. 

```
git clone https://github.com/jaimicore/InPreD_README.git
cd InPreD_README
```


## Dependencies (R packages)



```R
library(broom)
library(emo)
library(glue)
library(klippy)
library(rmarkdown)


# --------------------------- #
# List of required R packages #
# --------------------------- #
required.packages = c("broom",          
                      "emo",     
                      "glue",          
                      "klippy",       
                      "rmarkdown")       


for (lib in required.packages) {
  if (!require(lib, character.only = TRUE)) {
    install.packages(lib)
    suppressPackageStartupMessages(library(lib, character.only = TRUE))
  }
}
```



## Create interactive html README

&nbsp;

:warning: You need at least 32 GB of space to store the required files. (The compressed files requires 3.2 GB of space, and 28 GB once they are uncompressed).

:warning: Files downloaded on 2025-07-01

&nbsp;

The code assumes the user has a local copy of the following files.

  - *MAVEDB* scores: the scores for all experiments (*urn*s) are available through [zenodo record 15653325](https://zenodo.org/records/15653325). <br> Size: ~1.4 GB.
    - `csv/` : folder with csv files containing the scores of each variant
    - `LICENSE.txt`
    - `main.json` : metadata associated to each score file

  &nbsp;

  - *dcd-map* : the genomic mapping of each variant in *MAVEDB* is available thorough their [github repository](https://github.com/ave-dcd/dcd_mapping/tree/main). [Download mapping here](https://mavedb-mapping.s3.us-east-2.amazonaws.com/mappings_20250220.tar.gz). <br> Size: ~1.8 GB.
    -  `mappings_20250220/` : contains a json file mapping each variant in each urn to their genomic coordinates.

&nbsp;

Once you downloaded and uncompressed the required files, move them to the same folder (`mavedb_files` folder in this example), please use the following folder structure.

```
mavedb_files
│
├── csv
│   ├── urn-mavedb-00000001-a-1.scores.csv
│   ├── urn-mavedb-00000001-a-2.scores.csv
│   ├── urn-mavedb-00000001-a-3.scores.csv
│   ├── ...
│   └── urn-mavedb-00001240-a-3.scores.csv
│
│
├── LICENSE.txt
│
│
├── main.json
│
│
└── mappings_20250220
    │
    └── mappings
        ├── urn:mavedb:00000001-a-1_mapping_2025-02-19T14:10:14.622742+00:00.json
        ├── urn:mavedb:00000001-a-2_mapping_2025-02-19T14:12:34.979355+00:00.json
        ├── ...
        └── urn:mavedb:00001205-a-1_mapping_2025-02-21T05:07:02.501247+00:00.json
```

&nbsp;

## Download ensemble gene annotation

&nbsp;

The *dcd-map* mappings use *RefSeq* IDs, we provide a python script to download the annotation of the human protein coding genes.
Run this script once, before using *sailormave*. The output will be used to match the *RefSeq* IDs with the gene names 

  - Example: [NM_007294 -> BRCA1](https://www.ncbi.nlm.nih.gov/clinvar/RCV000696469/).

&nbsp;

How to run it?
(Assuming you are at the root directory of this repository)

  - *-g* : human genome version. Options: *hg19* or *hg38*
  - *-o* : output filename

&nbsp;

```bash
python src/get_human_pcg_annotation.py -g hg19 -o hg19_protein_coding_annotation.txt
```





