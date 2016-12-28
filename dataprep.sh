#!/bin/sh

Rscript R/runAnalisis.R
Rscript R/extractData.R
python dataprep.py