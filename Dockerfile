FROM hlapp/rpopgen
MAINTAINER forest.bremer@gmail.com

# anaconda3

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/archive/Anaconda3-4.2.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh

RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean

ENV PATH /opt/conda/bin:$PATH

# webapp

RUN conda install -y pyproj
#RUN conda install -y -c r r
#RUN apt-get update && apt-get install -y build-essential
#RUN R -e 'install.packages("adegenet", dep=TRUE, repos="http://cran.us.r-project.org")'


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