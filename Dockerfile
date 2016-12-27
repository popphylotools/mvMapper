FROM continuumio/anaconda3
MAINTAINER forest.bremer@gmail.com

RUN conda install -y pyproj

ENV BOKEH_APP /bokeh/dapc_webapp/
ENV APP_URL localhost
ENV APP_PORT 5006

EXPOSE 5006
WORKDIR /bokeh

COPY dapc_webapp /bokeh/dapc_webapp
COPY data /bokeh/data
COPY webapp.sh /bokeh/
COPY dataprep.sh /bokeh/

CMD ["sh", "webapp.sh"]