# InPreD bioinformatic pipeline README

&nbsp;

In this repository you will find a detailed explanation of all the steps required to run the InPreD bioinformatics pipeline (*Ahus* node), this includes the followings points:

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

&nbsp;

### 2.  Install R dependencies


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

&nbsp;

### 3. Create interactive html README and Checklist

&nbsp;
   
#### Ahus-OUS pipeline

Due to changes in the logistics, we adapted the InPreD pipeline so *LocalApp* is ran by *OUS* and the follwoing steps by *Ahus* (us).
The pipeline and checklist slightly differs as we need to run different steps, use the following command to generate the README.

You just need to pass the run ID and the command will create:

  - *README* in html
  - Interactive html checklist

NOTE: the checklist is not anymore generated within the `.Rmd` file. The checklist html document was externally generated using [this tool](https://jaimicore.shinyapps.io/html-checklist-generator/) and we simply copy-paste the template (when the `.Rmd` file is executed). If the checklist items are updated, we have to create a new html template.

&nbsp;

```bash
# Define RUN_ID
RUN_ID='250606_AAAAAAAA_BBBB_CCCCCCCCCC'

# Date is taken from RUN_ID
RUN_ID_DATE="${RUN_ID%%_*}"

# RUN_ID is passed as an argument to the RMD file
Rscript -e "rmarkdown::render(input = 'InPreD_pipeline_OUS-Ahus_README.Rmd', output_file = paste0('InPreD_pipeline_OUS-Ahus_README_','${RUN_ID_DATE}','.html'), params=list(args='${RUN_ID}'))"
```

&nbsp;

#### Ahus pipeline (used until 16-02-2026)

The interactive README file can be created in two ways:

  - Via *RStudio IDE*
    1. Open the `InPreD_README.Rmd` file with *RStudio*
    2. Click on the *knit* button (located on the top panel).
    
  - Command line
    1.  Requires `pandoc` to be installed in your machine. Installation in Ubuntu: `sudo apt-get install pandoc`
    2. `Rscript -e "rmarkdown::render('InPreD_README.Rmd')"`

&nbsp;

## Contributors

&nbsp;

- [Jaime A Castro-Mondragon](https://jaimicore.github.io/) (jamondra@uio.no)
- [Jean-Marc Costanzi](https://github.com/jean-marc-costanzi) (jean-marc.costanzi@ahus.no)
