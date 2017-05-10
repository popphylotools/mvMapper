FROM continuumio/anaconda3
MAINTAINER forest.bremer@gmail.com

RUN conda install -y pyproj
RUN conda install -y colorcet
RUN pip install pytoml

ENV APP_URL localhost
ENV APP_PORT 5006

EXPOSE 5006
WORKDIR /bokeh

COPY data /bokeh/data
COPY data /bokeh/config
COPY dapc_webapp /bokeh/dapc_webapp

VOLUME ["/bokeh/data"]
VOLUME ["/bokeh/config"]

COPY entrypoint.sh /bokeh/

CMD ["sh", "entrypoint.sh"]
