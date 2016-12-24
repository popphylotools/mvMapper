# consult: https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#/add-or-copy
FROM continuumio/anaconda3
MAINTAINER forest.bremer@gmail.com

ENV BOKEH_APP /bokeh/dapc_webapp/
ENV APP_URL localhost
ENV APP_PORT 5006

EXPOSE 5006
WORKDIR /bokeh

COPY dapc_webapp /bokeh/dapc_webapp
COPY data /bokeh/data
COPY entrypoint.sh /bokeh/

CMD ["sh", "entrypoint.sh"]