FROM continuumio/anaconda3
MAINTAINER forest.bremer@gmail.com

RUN conda install -y pyproj
RUN conda install -y -c r r

ENV BOKEH_APP /bokeh/dapc_webapp/
ENV APP_URL localhost
ENV APP_PORT 5006

EXPOSE 5006
WORKDIR /bokeh

COPY dapc_webapp /bokeh/dapc_webapp
COPY data /bokeh/data
COPY R /bokeh/R
COPY python /bokeh/python

VOLUME ["/bokeh/data"]

COPY entrypoint.sh /bokeh/

CMD ["sh", "entrypoint.sh"]