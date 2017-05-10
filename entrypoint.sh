#!/bin/sh

# if we have mvmapper_input.csv, run webapp
if [ -e "data/mvmapper_input.csv" ] && [ -e "config/config.toml" ]
then
    bokeh serve /bokeh/dapc_webapp/ --host ${APP_URL}:${APP_PORT} --port 5006
fi
