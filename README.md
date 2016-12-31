dapc_webapp
===========
This webapp serves as an interactive data exploration tool for popgen data analized with the dapc function of the R library Adegenet. This webapp also requires associated location information and supports additional metadata. It displays a scatterplot with selecters for z-axis, y-axis, point color, and point size, in addition to a worldmap. Data selections are linked across the two plots, and a data table below shows details of the selected data.

Prepairing data
---------------
This webapp is designed to consume data created with the R library Adegenet. The particulars of this process go beond the scope of this document, however a tutorial is avalible [here](adegenet.r-forge.r-project.org/files/tutorial-dapc.pdf)

Once you have run the dapc analisis and have a dapc object in R, say `dapc1`, you can save it by running `saveRDS(dapc1, file="dapc.rds")`

You must then create a location.csv file which, at minimum, includes a `key` column matching the keys used in the input for the dapc analisis, as well as `Lat` and `Lng` columns containing the decimal coordinates assosiated with that sample.

you can include additional columns of information which will be ingested and displayed within the webapp.

Runing in Docker
----------------
Run with sample data:
```
docker run -d -p 5006:5006 woods26/dapc_webapp
```

Run with daps.rds and location.csv in <absolute_path_to_local_data_dir>
```
docker run -d -p 5006:5006 -v <absolute_path_to_local_data_dir>:/bokeh/data woods26/dapc_webapp
```


Running localy
--------------
In order to run locally I would sugest following the install process outlined in the Dockerfile. I reccomend installing Anaconda3, then using conda to install pyproj and R if your system doesn't already have it.


Example Data
------------
Example data (783 autosomal microsatellite loci genotyped for 1048 individuals from 53 populations) from 
Rosenberg NA, Mahajan S, Ramachandran S, Zhao C, Pritchard JK, Feldman MW (2005) Clines, clusters, and the effect of study design on the inference of human population structure. PLoS Genetics 1:660-671.
Available from <https://rosenberglab.stanford.edu/diversity.html>