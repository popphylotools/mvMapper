# get docker from dockerhub
docker pull woods26/dapc_webapp

# or build yourself
docker build -t dapc_webapp ./

# then run with daps.rds and location.csv in <local_data_dir>
docker run -d -p 5006:5006 -v <local_data_dir>:/bokeh/data dapc_webapp

# or run interactively for analisis
docker run -t -i -p 5006:5006 -v <local_data_dir>:/bokeh/data dapc_webapp bash