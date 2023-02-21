
## Original setup steps - deprecated

These are the original steps to install Postgres + PostGIS on your mac directly. However, I don't recommend it anymore 
since it's brittle when packages upgrade.

`brew install gdal geos` - geospatial libraries. 
Check [supported versions](https://docs.djangoproject.com/en/4.1/ref/contrib/gis/install/geolibs/) 
in Django docs if you have problems.

~~`brew install python3` - use python 3.9 or newer~~ - replaced by pyenv below.

`pip3 install geopandas` - adds support for geographic data to pandas objects

`brew install pipx` - pipx is a tool for installing and running Python applications in isolated environments

`brew pin gdal geos pipx geos ` - pin gdal and pipx so they don't get upgraded

* `brew install postgresql@14`

* `brew install postgis` - PostgreSQL extension for geometry types and geospatial functions. Installs it with the protobuf support compiled in.

* `brew pin postgresql@14 postgis ` - pin packages so they don't get upgraded

`pipx ensurepath` - makes sure pipx is in your path  

From the project directory:
`cp .env.example .env` -- create your .env file.

Depending on your setup, you might need to add library paths as follows to your .zshrc or other shell init file (adjusting version numbers as required):
* `export GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.1.17.0.dylib`
* `export GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.31.dylib`

* `brew services start postgres` -- Run the Postgres server as a service in the background

* `createdb geodjango` -- postgres command to create the database

* `./manage.py migrate` -- apply django migrations to the local DB

* `./manage.py createsuperuser` -- give yourself a superadmin account on django

The above is mostly a one-time setup. 
