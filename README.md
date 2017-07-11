Intro
=====

This webapp serves as an interactive data exploration tool for multi-variate analyses with associated geographic location information.
The provided example data set and configuration file demonstrate its use with population genetic data analyzed with discriminant
analysis of principal components (DAPC) in the R library adegenet. It displays a scatterplot with selectors for x-axis, y-axis,
point color, point size, and color pallet in addition to a world map with optional jitter to separate stacked points.
Data selections are linked across the two plots, and a data table below shows details of the selected data, which can also be downloaded as a csv.
The bottom of the page contains an upload interface for user generated data files.

Pipeline
========

Here we show an example pipeline using **mvMapper** with **DAPC** in **adegenet**.
For more details on the DAPC, see its [tutorial](https://github.com/thibautjombart/adegenet/raw/master/tutorials/tutorial-dapc.pdf).

The export_to_webapp function in adegenet combines data from commonly-used multivariate analyses with
location information and supplementary data. The resulting data structure can be easily output as a CSV which is taken as input to our web app. This function currently supports multivariate analyses conducted in adegenet and those based on the duality diagram (dudi. functions) in ade4.

In the following example, we conduct DAPC and create an R object called `dapc1`.
We then read in locality information from `localities.csv`, and combine the two using the export_to_webapp function before writing `rosenbergData.csv`, which is the input file for mvMapper.
This localities file can include additional columns of information that will be ingested and displayed within the web app (e.g. host, sex, morphological characteristics).
The resulting csv can be uploaded through the web app's upload interface, or configured as the default data file when running a stand-alone version of mvMapper.

```r
> # An example using the microsatellite dataset of Rosenberg et al. 2005
> # Using adegenet 2.0.1
> # Reading input file
> Rosenberg <- read.structure("Rosenberg_783msats.str", n.ind=1048, n.loc=783,  onerowperind=F, col.lab=1, col.pop=2, row.marknames=NULL, NA.char="-9", ask=F, quiet=F)

> # DAPC (n.pca determined using xvalDapc, see ??xvalDapc)
> dapc1 <- dapc(Rosenberg, n.pca=20, n.da=200)

> # read in localities.csv, which contains “key”, “lat”, and “lon” columns with column headers (this example contains a fourth column “population” which is a text-based population name based on geography)
> localities <- read.csv(file=”localities.csv”, header=T)

> # generate mvmapper input file and write to “rosenbergData.csv”
> out <- export_to_webapp(dapc1,localities)
> write.csv(out, “rosenbergData.csv”, row.names=F)
```

Input Files
===========

The web app uses `webapp/data` and `webapp/config` directories for user provided data and configuration files.
These files can be selected by adding their file names as optional parameters to the URL following the form:

```bash
<base_url>/?c=<config_filename>&d=<data_filename>
```

Data
-----

This webapp is built to be modular and generalized.
Because of this, it is relatively easy to adapt it to visualize data from other analyses.
The webapp consumes a csv file that, at minimum, includes a `key` column (individual identifiers),
as well as `lat` and `lon` columns containing the decimal coordinates associated with each sample.
Additional columns are optional.

Config
------

The provided config file sets the webapp up for use with the results from a DAPC analysis.

```toml
# config for adegenet dapc analysis results

# location of default data file
defaultDataPath = "data/rosenbergData.csv"

# default selection for X-Axis dropdown widget
default_xAxis = "PC1"

# default selection for Y-Axis dropdown widget
default_yAxis = "PC2"

# default selection for Color dropdown widget
default_colorBy = "assigned_grp"

# default selection for Palette dropdown widget
default_palette = "inferno"

# default selection for Size dropdown widget
default_sizeBy = "support"

# This value determins what discrete (non-numeric) colomns will be avalible in the "Color" dropdown.
# This can be used to prevent coloring by a column with a large number of unique discrete values which would cause
# adjacent colors to be visually indistinguishable.
max_discrete_colors = 255

# columns named here will be treated as discrete even if numeric and will be added to discrete_colorable regardless
# of value of max_discrete_colors as long as they contain less then 256 unique values (max of color palette).
force_discrete_colorable = ["grp", "assigned_grp"]

# coordinates applpied when location information is missing
[default_coords]
    lon = 0
    lat = -80
```

Run Using Docker
================

If you have an os that supports [Docker](https://www.docker.com/) and you have root access, docker can provide a straightforward install process.

On systems which run docker in a virtual machine (such as older windows systems), mvMapper will need to be served as if it's being accessed remotely.

Install
-------

Once docker is installed, installation of mvMapper is as easy as:

```bash
docker pull genomeannotation/mvmapper
```

Building the docker locally from source is relatively easy as well.

```bash
git clone https://github.com/genomeannotation/mvMapper.git
cd mvMapper
docker build -t genomeannotation/mvmapper:local_build .
```

Serve
-----

For local access, by default, the webapp can be accessed at `localhost:5006`.
Simply run the mvMapper docker in demon mode and forward port 5006 to the host:

```bash
docker run -d \
-p 5006:5006 \
genomeannotation/mvmapper:latest
```

If data and config directories are to be managed from the host, host directories can be mounted in place of the containers data and config volumes.
Note that `rosenbergData.csv` should be placed in the data directory as host directories will not have files automatically copied into them.

```bash
docker run -d \
-p 5006:5006 \
-v <absolute_path_to_host_data_dir>:/mvMapper/data \
-v <absolute_path_to_host_config_dir>:/mvMapper/config \
genomeannotation/mvmapper:latest
```

For remote access, the default `APP_URL` and `APP_PORT` environmental variables need to be redefined to reflect the address and port at which the web app should be accessible.

```bash
docker run -d \
-p <port_at_which_app_will_be_accessed>:5006 \
-e "APP_URL=<url_at_which_app_will_be_accessed>" \
-e "APP_PORT=<port_at_which_app_will_be_accessed>" \
-v <absolute_path_to_host_data_dir>:/mvMapper/data \
-v <absolute_path_to_host_config_dir>:/mvMapper/config \
genomeannotation/mvmapper:latest
```

If it is desirable for old uploaded user data to be deleted, set the `DAYS_TO_KEEP_DATA` environment variable in the docker run command.
For instance, to delete user uploaded data after 2 weeks, add the following line to the above docker run command:

```bash
-e "DAYS_TO_KEEP_DATA=14" \
```

Note that the cron job that handles deletion will ignore file names containing a `.`.
Data files uploaded through the web interface are assigned a random name with no extension and will thus be affected,
whereas data files added manually should be given the extension `.csv` and will be left alone.

Run Without Docker
==================

When running mvMapper on systems which do not support docker, the `Dockerfile` can be followed as a guide.

Install
-------

We support installation of dependencies as an anaconda environment using the provided environment.yml.

Once [Anaconda](https://docs.continuum.io/anaconda/install/) is installed:

```bash
git clone https://github.com/genomeannotation/mvMapper.git
cd mvMapper
conda env create
```

Serve
-----

To run mvMapper, activate the conda env, then run main.py with the appropriate parameters.

```bash
source activate mvmapper
python webapp/main.py <url_at_which_app_will_be_accessed>:<port_at_which_app_will_be_accessed> <port_at_which_app_will_be_accessed>
```

For local access for instance, the final command will be `python main.py localhost:5006 5006`

Example Data
============

Example data (783 autosomal microsatellite loci genotyped for 1048 individuals from 53 populations) from 
Rosenberg NA, Mahajan S, Ramachandran S, Zhao C, Pritchard JK, Feldman MW (2005) Clines, clusters, and the effect of study design on the inference of human population structure. PLoS Genetics 1:660-671.
Available from <https://rosenberglab.stanford.edu/diversity.html>
