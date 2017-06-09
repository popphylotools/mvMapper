#!/bin/sh

# if we have mvmapper_input.csv, run webapp
if [ -e "exampleData/mvmapper_input.csv" ] && [ -e "config/config.toml" ]
then
    python main.py ${APP_URL} ${APP_PORT}
fi
