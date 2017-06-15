FROM continuumio/anaconda3
MAINTAINER forest.bremer@gmail.com

RUN conda update -y bokeh
RUN conda install -y pyproj
RUN conda install -y colorcet
RUN pip install pytoml

ENV APP_URL localhost
ENV APP_PORT 5006

EXPOSE 5006

COPY mvMapper /mvMapper
WORKDIR /mvMapper

VOLUME ["/mvMapper/data"]
VOLUME ["/mvMapper/config"]

CMD ["sh", "entrypoint.sh"]
