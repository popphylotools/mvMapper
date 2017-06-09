#!/bin/sh

# create data dir for user data if it doesn't exist
mkdir -p data

# if we have mvmapper_input.csv, and config.toml, run webapp
if [ -e "exampleData/mvmapper_input.csv" ] && [ -e "config/config.toml" ]
then
    python main.py ${APP_URL}:${APP_PORT} 5006
fi
