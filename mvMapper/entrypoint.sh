#!/bin/sh

# if we have mvmapper_input.csv, run webapp
if [ -e "data/mvmapper_input.csv" ] && [ -e "config/config.toml" ]
then
    python main.py
fi
