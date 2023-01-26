# ARG PYTHON_VERSION=3.9
# FROM python:${PYTHON_VERSION}

# Ubuntu 20.04 LTS std support until April 2025, EOL April 2030.
# focal = Ubuntu 20.04 LTS *** our current version
# jammy = Ubuntu 22.04 LTS - was released April 2022
FROM ubuntu:20.04

### INSTALL SYSTEM PACKAGES ##############################################################

# Deadsnakes repo needed for python 3.9
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

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
    && apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

    # postgresql-client=12+214ubuntu0.1

RUN chsh -s /usr/bin/bash
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app

### INSTALL NODE AND PYTHON PKG MANAGERS #################################################

RUN npm install --location=global yarn

RUN curl -sSL https://install.python-poetry.org | python3.9 - --version 1.2.2

### INSTALL SUPERCRONIC CRON MANAGER #####################################################

# Supercronic setup, as per fly.io: https://fly.io/docs/app-guides/supercronic/
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.1/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=d7f4c0886eb85249ad05ed592902fa6865bb9d70

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

COPY crontab crontab

### PYTHON DEPENDENCIES ##################################################################
# Set up a python virtual env for all subsequent commands
ENV BUILD_PHASE=True
ENV DJANGO_ENV=production

# Do python package installations first, so that they're cached in most cases
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Do frontend package installations before copying files too, so they're cached.
RUN mkdir frontend
WORKDIR /app/frontend
COPY frontend/package.json .
COPY frontend/yarn.lock .
RUN yarn install && yarn cache clean

# Copy source code - put as late as possible in file, since it's fast-changing.
WORKDIR /app
COPY . .
RUN mkdir -p dist/static
RUN poetry run python manage.py collectstatic --noinput


### FRONT-END INSTALL AND BUILD ##########################################################
WORKDIR /app/frontend
RUN yarn build

WORKDIR /app
EXPOSE 8080

### EXECUTE THE APP SERVER ###############################################################

# NOTE: I believe this is overridden by fly.toml's processes list
CMD ["poetry", "run", "gunicorn", "--bind", ":8080", "--workers", "3", "mygeo.wsgi:application"]
# CMD ["sleep", "999999"]

### THE END ##############################################################################
