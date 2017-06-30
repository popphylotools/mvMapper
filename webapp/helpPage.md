Multivariate Mapper
===================

**mvMapper** is an interactive data exploration tool for multivariate analyses with associated geographic location information. Although we developed mvMapper with population genetic data in mind, it will ingest results of virtually any multivariate analysis of georeferenced data. mvMapper’s greatest strength is facilitating dynamic exploration of the statistical and geographic frameworks side-by-side, a task that is difficult and time-consuming to do in static space. It displays a scatterplot with selectors for x-axis, y-axis, point color, point size, and color pallet in addition to a world map with optional jitter to separate stacked points. Data selections are linked across the two plots, and a data table below shows details of the selected data, which can also be downloaded as a csv.

The input format is a simple comma-delimited tabular file (.CSV) that can either be assembled manually, or generated using mvMapper’s input generation function in the adegenet library (export_to_webapp). This function currently supports multivariate analyses conducted in adegenet and those based on the duality diagram (dudi. functions) in ade4, including principal components analysis (regular and spatial varieties), discriminant analysis of principal components, principal coordinates analysis, non-metric dimensional scaling, and correspondence analysis.

Below, we provide an example of a general workflow (data preparation), and usage instructions for the web interface of mvMapper.

General Workflow: Data Prep
===========================

Here we show an example pipeline using **mvMapper** with **DAPC** in **adegenet**.
For more details on the DAPC, see its [tutorial](https://github.com/thibautjombart/adegenet/raw/master/tutorials/tutorial-dapc.pdf).

Example data (783 autosomal microsatellite loci genotyped for 1048 individuals from 53 populations) from
Rosenberg NA, Mahajan S, Ramachandran S, Zhao C, Pritchard JK, Feldman MW (2005) Clines, clusters, and the effect of study design on the inference of human population structure. PLoS Genetics 1:660-671.
Available from <https://rosenberglab.stanford.edu/diversity.html>

The `export_to_webapp` function in adegenet combines data from commonly-used multivariate analyses with
location information and supplementary data. The resulting data structure can be easily output as a CSV which is taken as input to our web app. At a minimum, the input to mvMapper must include three columns: `key` (individual identifiers),
and `lat` and `lon` (containing the decimal coordinates associated with each sample). Additional columns are optional.

| key | lat | lon |
| --- | --- | --- |
| 1 | 30.49871492 | 66.5 |
| 99 | 33.49855601 | 70 |
| 130 | 26 | 64 |
| 163 | 25.49063551 | 69 |
| 213 | 33.48700562 | 70.5 |

In the following example, we conduct DAPC and create an R object called `dapc1`.
We then read in locality information from `localities.csv`, and combine the two using the `export_to_webapp` function before writing `rosenbergData.csv`, which is the input file for mvMapper.
This localities file can include additional columns of information that will be ingested and displayed within the web app (e.g. host, sex, morphological characteristics).
The resulting CSV file can be uploaded through the web app's upload interface, or configured as the default data file when running a stand-alone version of mvMapper.

```r
# An example using the microsatellite dataset of Rosenberg et al. 2005
# Using adegenet 2.0.1
# Reading input file
Rosenberg <- read.structure("Rosenberg_783msats.str", n.ind=1048, n.loc=783,  onerowperind=F, col.lab=1, col.pop=2, row.marknames=NULL, NA.char="-9", ask=F, quiet=F)

# DAPC (n.pca determined using xvalDapc, see ??xvalDapc)
dapc1 <- dapc(Rosenberg, n.pca=20, n.da=200)

# read in localities.csv, which contains “key”, “lat”, and “lon” columns with column headers (this example contains a fourth column “population” which is a text-based population name based on geography)
localities <- read.csv(file=”localities.csv”, header=T)

# generate mvmapper input file and write to “rosenbergData.csv”
out <- export_to_webapp(dapc1,localities)
write.csv(out, “rosenbergData.csv”, row.names=F)
```

Web Use
=======

Once you have a CSV input file, such as the one generated above, it can be uploaded to the web interface via the upload interface at the bottom of the page (either drag and drop, or select through the navigation button). When a file is uploaded, it is assigned a random alphanumeric string, and a link is provided to the mvMapper instance for that datafile. This instance is saved on the web server for 14 days, and can be returned to using the web address provided in the link.

Example Data
============

Example data (783 autosomal microsatellite loci genotyped for 1048 individuals from 53 populations) from
Rosenberg NA, Mahajan S, Ramachandran S, Zhao C, Pritchard JK, Feldman MW (2005) Clines, clusters, and the effect of study design on the inference of human population structure. PLoS Genetics 1:660-671.
Available from <https://rosenberglab.stanford.edu/diversity.html>