FROM continuumio/miniconda3
MAINTAINER forest.bremer@gmail.com

# Set the ENTRYPOINT to use bash
# (this is also where you’d set SHELL,
# if your version of docker supports this)
ENTRYPOINT [ "/bin/bash", "-c" ]

EXPOSE 5006

# Use the environment.yml to create the conda environment.
ADD environment.yml /tmp/environment.yml
WORKDIR /tmp
RUN [ "conda", "env", "create" ]

COPY mvMapper /mvMapper
WORKDIR /mvMapper

VOLUME ["/mvMapper/data"]
VOLUME ["/mvMapper/config"]

ENV APP_URL localhost
ENV APP_PORT 5006

CMD ["mkdir -p config && mkdir -p data && source activate mvmapper && python main.py ${APP_URL}:${APP_PORT} 5006"]