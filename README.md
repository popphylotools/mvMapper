dapcmapper
===========
This webapp serves as an interactive data exploration tool for population genetic data analyzed with discriminant analysis of principal components (DAPC) in the R library adegenet. This webapp also requires associated location information and supports additional metadata. It displays a scatterplot with selectors for x-axis, y-axis, point color, and point size, in addition to a worldmap with optional jitter to seperate stacked points. Data selections are linked across the two plots, and a data table below shows details of the selected data, which can also be downloaded as a csv.

Pipeline
--------
This webapp is built to be modular and generalized. Because of this, it would be relitively easy to adapt it to visualize data from another analisis. The webapp itself actually consumes a csv called `webapp_input.csv` Which is only required to have `key`, `lat`, and `lng` columns as described below in the section partaining to `location.csv`. Additional colomns are optional. The preperation pipeline consists of two scripts. The first is an R script that simply dumps the tables from `dapc.rds` to `.csv`'s. The second is a python script which: collects colomns of interest from these `.csv`'s, synthisises additional colomns from data in these `.csv`'s, and finally merges in the seperatly provided location information from `location.csv`. The flow of the pipeline is orchestrated by `entrypoint.sh`.

Preparing data
---------------
This webapp pipeline is designed to consume a DAPC data object created with the R library adegenet. The particulars of that analisis go beyond the scope of this document, however a tutorial is available [here](adegenet.r-forge.r-project.org/files/tutorial-dapc.pdf)

Once you have run the DAPC and have an active DAPC object in R, for example called `dapc1` in following the DAPC tutorial, you can save it by running `saveRDS(dapc1, file="dapc.rds")`

You must then create a location.csv file that, at minimum, includes a `key` column matching the keys (individual identifiers) used in the input for the DAPC, as well as `Lat` and `Lng` columns containing the decimal coordinates associated with each sample.

you can include additional columns of information which will be ingested and displayed within the webapp (e.g. host, sex, morphological characteristics, etc.).

Running dapcmapper in [Docker](https://www.docker.com/)
----------------
Run with example data (see below):
```
docker run -d -p 5006:5006 woods26/dapc_webapp:latest
```
Then just open a web browser, and navigate to `localhost:5006`



Run with dapc.rds and location.csv in <absolute_path_to_local_data_dir> for your own data
```
docker run -d -p 5006:5006 -v <absolute_path_to_local_data_dir>:/bokeh/data woods26/dapc_webapp:latest
```

Building and running docker locally
-----------------------------------
If you want to make changes and build/run docker locally, you can use the following commands:
```docker build -t woods26/dapc_webapp:local <path to cloned git repo>
docker run -d -p 5006:5006 woods26/dapc_webapp:local```


Running localy without docker
-----------------------------
In order to run locally without docker I would sugest following the install process outlined in the Dockerfile as a guide. I reccomend installing Anaconda3, then using conda to install pyproj and R if your system doesn't already have it.


Example Data
------------
Example data (783 autosomal microsatellite loci genotyped for 1048 individuals from 53 populations) from 
Rosenberg NA, Mahajan S, Ramachandran S, Zhao C, Pritchard JK, Feldman MW (2005) Clines, clusters, and the effect of study design on the inference of human population structure. PLoS Genetics 1:660-671.
Available from <https://rosenberglab.stanford.edu/diversity.html>
