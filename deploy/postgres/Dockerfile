FROM postgres:14-bullseye

LABEL maintainer="PostGIS Project - https://postgis.net"

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.2.2+dfsg-1.pgdg110+1

# RUN mkdir /pgdata/data && chown postgres:postgres /pgdata/data && chmod og+rx /pgdata

# Mount external volume for postgres data.
# For this to work, /pgdata/data must exist, be chown'd to postgres:postgres, and have
# chmod og+rx on /pgdata too
ENV PGDATA /pgdata/data

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d


## Password comes from secret instead of being hardcoded (so don't uncomment this)
# ENV POSTGRES_PASSWORD supersecret

COPY ./initdb-postgis.sh /docker-entrypoint-initdb.d/10_postgis.sh
COPY ./update-postgis.sh /usr/local/bin

# CMD ["sleep", "infinity"]
