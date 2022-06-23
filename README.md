# h3-gis
GIS application

# Setup steps
This is currently working on a Mac with M1 processor. Will need tweaks for other environments.

`brew install gdal` - translator library for raster and vector geospatial data formats
`brew install python3` - use python 3.8 or newer

From the project directory:
`python3 -m venv ./venv` to create a venv ([ref](https://docs.python.org/3/library/venv.html))
`source ./venv/bin/activate` to put local python and site-packages in path.
`pip install -r requirements.txt`

... A couple steps to setup DB which we should document...

`./manage.py runserver` - start django server. 
Browse to http://localhost:8000/map or http://localhost:8000/admin . 
