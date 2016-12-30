# run with sample data
docker run -d -p 5006:5006 woods26/dapc_webapp

# run with daps.rds and location.csv in <local_data_dir>
docker run -d -p 5006:5006 -v <local_data_dir>:/bokeh/data woods26/dapc_webapp

# or run interactively
docker run -t -i -p 5006:5006 -v <local_data_dir>:/bokeh/data woods26/dapc_webapp bash