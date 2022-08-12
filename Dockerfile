# ARG PYTHON_VERSION=3.9
# FROM python:${PYTHON_VERSION}

# Ubuntu 20.04 LTS std support until April 2025, EOL April 2030.
FROM ubuntu:20.04

RUN apt update && apt install -y software-properties-common

# Deadsnakes repo needed for python 3.9
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y curl

# Get Node 16.x - EOL Sept 2023
# NODEJS distributions from nodesource.com
# https://github.com/nodesource/distributions/blob/master/README.md
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -


RUN apt-get update && apt-get install -y \
    nodejs \
    gdal-bin \
    libgdal-dev

RUN apt-get install -y \
    python3.9 \
    python3.9-distutils \
    python3.9-venv \
    python3.9-dev 
#    python3.9-wheel \
#     python3-setuptools \
#     python3-wheel \


RUN mkdir -p /app
WORKDIR /app

# Set up a virtual env for all subsequent commands
ENV VIRTUAL_ENV=/app/venv
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# COPY . .

ENV BUILD_PHASE=True
ENV DJANGO_ENV=production
# RUN python manage.py collectstatic --noinput

WORKDIR /app/frontend
# RUN yarn install
# RUN yarn build

WORKDIR /app
EXPOSE 8080

# CMD sh
# CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "mygeo.wsgi:application"]
CMD ["sleep", "infinity"]
