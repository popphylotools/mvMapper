#!/bin/sh

if ! [ -e "data/dapc.rds" ] && ! [ -e "data/webapp_data.csv" ]
then
    Rscript R/runAnalisis.R
fi

if ! [ -e "data/webapp_data.csv" ] && [ -e "data/location.csv" ] && [ -e "data/dapc.rds" ]
then
    Rscript R/extractData.R
    python python/dataprep.py
fi

if [ -e "data/webapp_data.csv" ]
then
    bokeh serve $BOKEH_APP --host $APP_URL:$APP_PORT --port $APP_PORT
fi