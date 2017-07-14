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

COPY webapp /webapp
WORKDIR /webapp

VOLUME ["/webapp/data"]
VOLUME ["/webapp/config"]

ADD deleteOldServerData.sh /etc/cron.daily
RUN chmod +x /etc/cron.daily/deleteOldServerData.sh

ENV APP_URL localhost
ENV APP_PORT 5006
ENV DAYS_TO_KEEP_DATA 0 # zero keeps data forever. only filenames with no extension are affected by cron

CMD ["source activate mvmapper && python main.py --host ${APP_URL}:${APP_PORT} --port 5006"]