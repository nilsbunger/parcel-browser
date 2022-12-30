# ARG PYTHON_VERSION=3.9
# FROM python:${PYTHON_VERSION}

# Ubuntu 20.04 LTS std support until April 2025, EOL April 2030.
# focal = Ubuntu 20.04 LTS *** our current version
# jammy = Ubuntu 22.04 LTS - was released April 2022
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
    gdal-bin=3.0.4+dfsg-1build3 \
    libgdal-dev=3.0.4+dfsg-1build3 \
    python3.9 \
    python3.9-distutils \
    python3.9-venv \
    python3.9-dev \
    openssh-client \
    postgresql-client=12+214ubuntu0.1

RUN npm install --location=global yarn

RUN chsh -s /usr/bin/bash

# RUN pip install "poetry==$POETRY_VERSION"
RUN curl -sSL https://install.python-poetry.org | python3.9 - --version 1.2.2
ENV PATH="/root/.local/bin:$PATH"


WORKDIR /app

# Set up a python virtual env for all subsequent commands
# ENV VIRTUAL_ENV=/app/venv
# RUN python3.9 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV BUILD_PHASE=True
ENV DJANGO_ENV=production

# Do package installations first, so that they're cached in most cases
# RUN pip install wheel
# COPY requirements.txt .
# RUN pip install -r requirements.txt
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY . .
RUN mkdir -p dist/static
RUN poetry run python manage.py collectstatic --noinput

WORKDIR /app/frontend
RUN yarn install && yarn cache clean
RUN yarn build

WORKDIR /app
EXPOSE 8080

CMD ["poetry", "run", "gunicorn", "--bind", ":8080", "--workers", "3", "mygeo.wsgi:application"]
# CMD ["sleep", "999999"]
