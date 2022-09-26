# ARG PYTHON_VERSION=3.9
# FROM python:${PYTHON_VERSION}

# Ubuntu 20.04 LTS std support until April 2025, EOL April 2030.
FROM ubuntu:20.04

# Deadsnakes repo needed for python 3.9
RUN apt update && apt install -y \
    software-properties-common \
    curl
RUN add-apt-repository ppa:deadsnakes/ppa

# Get Node 16.x - EOL Sept 2023
# NODEJS distributions from nodesource.com
# https://github.com/nodesource/distributions/blob/master/README.md
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -

# openssh-client -- for ssh and scp to work
# postgresql-client -- for psql
RUN apt-get update && apt-get install -y \
    nodejs \
    gdal-bin \
    libgdal-dev \
    python3.9 \
    python3.9-distutils \
    python3.9-venv \
    python3.9-dev \
    openssh-client \
    postgresql-client

RUN npm install --location=global yarn

RUN chsh -s /usr/bin/bash

WORKDIR /app

# Set up a python virtual env for all subsequent commands
ENV VIRTUAL_ENV=/app/venv
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV BUILD_PHASE=True
ENV DJANGO_ENV=production

# Do package installations first, so that they're cached in most cases
RUN pip install wheel
COPY requirements.txt .
RUN pip install -r requirements.txt
# WORKDIR /app/frontend
# COPY frontend/package.json .

COPY . .
RUN mkdir -p dist/static
RUN python manage.py collectstatic --noinput

WORKDIR /app/frontend
RUN yarn install && yarn cache clean
RUN yarn build

WORKDIR /app
EXPOSE 8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "mygeo.wsgi:application"]
# CMD ["sleep", "999999"]
