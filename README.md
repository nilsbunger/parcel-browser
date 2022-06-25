# h3-gis
GIS application

# Setup steps
This is currently working on a Mac with M1 processor. Will need tweaks for other environments.

`brew install gdal` - translator library for raster and vector geospatial data formats

`brew install python3` - use python 3.8 or newer

From the project directory:
`python3 -m venv ./venv` to create a venv ([ref](https://docs.python.org/3/library/venv.html))

`source ./venv/bin/activate` to put local python and site-packages in path.

`cp .env.example .env` -- create your .env file, get DB credentials from an admin.

# Install or update dependencies

`pip install -r requirements.txt`

`cd frontend && yarn add` -- install dependencies for frontned

# Running in dev
You'll need to run frontend and backend servers:

`cd frontend && yarn dev` -- start frontend (parcel) dev server
`./manage.py runserver` - start backend (django) server. 

Browse to http://localhost:8000/map or http://localhost:8000/admin . 

You'll periodically need to update python and yarn dependencies