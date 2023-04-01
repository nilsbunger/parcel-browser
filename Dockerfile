# ARG PYTHON_VERSION=3.9
# FROM python:${PYTHON_VERSION}

# Ubuntu 20.04 LTS std support until April 2025, EOL April 2030.
# focal = Ubuntu 20.04 LTS *** our current version
# jammy = Ubuntu 22.04 LTS - was released April 2022
FROM ubuntu:20.04

### INSTALL SYSTEM PACKAGES ##############################################################
RUN apt-get update \
    && apt-get install -y wget curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

### CONDA / MAMBA SETUP #################################################################
# Install Miniconda + Mamba and setup path
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

ENV PATH /opt/conda/bin:$PATH
WORKDIR /app

RUN conda install -y -c conda-forge mamba

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


### INSTALL AND ACTIVATE MAMBA ENVIRONMENT #####################################################
COPY mamba-env.yml .
RUN mamba env create -f mamba-env.yml \
# Install gcc for compiling psycopg2 (it's recommended to build from source for
# production)
  && mamba install -n parsnip gcc_linux-64 \
  && mamba init \
  && mamba clean -all -y

# Make all Docker RUN commands use the new environment:
SHELL ["conda", "run", "-n", "parsnip", "/bin/bash", "-c"]

### INSTALL YARN (requires conda env) ####################################################
RUN npm install --location=global yarn

### ENVIRONMENT - these variables are available in the build phase on Fly.io
ENV BUILD_PHASE=True
ENV REACT_APP_BACKEND_DOMAIN=https://parsnip.fly.dev
ENV DJANGO_ENV=production

### PYTHON DEPENDENCIES ##################################################################

# Do python package installations first, so that they're cached in most cases
COPY crontab crontab
COPY pyproject.toml .
COPY poetry.toml .
COPY poetry.lock .
RUN poetry install --only main --no-root --no-interaction --no-ansi

### FRONTEND DEPENDENCIES ##################################################################
# Do frontend package installations before copying files too, so they're cached.
RUN mkdir frontend
WORKDIR /app/frontend
COPY frontend/package.json .
COPY frontend/yarn.lock .
RUN yarn install && yarn cache clean

### COPY FRONTEND AND BACKEND SOURCE CODE ##################################################
# Copy source code - put as late as possible in file, since it's fast-changing.
WORKDIR /app
COPY . .

RUN mkdir -p dist/static && python manage.py collectstatic --noinput
### FRONT-END BUILD ##########################################################
WORKDIR /app/frontend
RUN yarn build

WORKDIR /app
EXPOSE 8080

### EXECUTE THE APP SERVER ###############################################################

# NOTE: I believe this is overridden by fly.toml's processes list
# CMD ["poetry", "run", "gunicorn", "--bind", ":8080", "--workers", "3", "mygeo.wsgi:application"]
# CMD ["sleep", "999999"]
