#!/bin/sh

if ! [ -e "data/webapp_data.csv" ] && [ -e "data/location.csv" ] && [ -e "data/dapc.rds" ]
then
    Rscript scripts/extractData.R
    python scripts/dataprep.py
fi

if [ -e "data/webapp_data.csv" ]
then
    bokeh serve $BOKEH_APP --host $APP_URL:$APP_PORT --port $APP_PORT
fi