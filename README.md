# h3-gis
Home3 GIS application for evaluating parcels for upzoning.

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

# Management commands
In `world/management/commands/` you'll find our custom command-line commands for
doing ETL and various other processing. This is the easiest place to 
write code that isn't a web request.

You can add a new file in this
directory and it will magically become a Django mgmt command, eg 
`./manage.py <command> <params>`, where <command> is the name of the file you 
created.

# Importing data

You don't need this section if you're using data that's already loaded into our cloud DB. 
But if you're loading new data, or setting up a new DB, follow these instructions:

1. Put shape files from San Diego in world/data/ subdirectories. 
We currently recognize Parcels.zip, Building_outlines.zip, and Zoning_base_sd.zip
2. Load the shape files into the DB:
`./manage.py load Parcel`
`./manage.py load Buildings
`./manage.py load Buildings`
3. Run ETL jobs as necessary, eg:
`./manage.py analyze_parcels rebuild` - populates the analyze_parcels table

# Copying data from one DB to another

If you already have data set up in one DB, it might be faster to copy the 
table to another DB. 

## Using SQL clients
Using a SQL client to create and move a dump is pretty fast. Even the 3GB Parcel
table can be exported and imported in a few minutes.

Here's an example of copying from your local DB to our cloud DB:
1. Make sure the destination table is empty: `Delete from world_*` on the correct DB would work. Just be careful!
2. `pg_dump -a -t 'world_*' geodjango | gzip > world_dump.sql` where 'geodjango' is the local DB name and world_parcel is the DB table to export
4. Optional - Send the file to the remote machine to be close to the DB. Example for AcuGIS server:
    `scp -i id_rsa ../world_dump.sql.gz hgiswebg@us14.acugis-dns.com:~`
6. Load the file into the new DB. Example for AcuGIS server:
    `gunzip -c world_dump.sql.gz | psql -U hgiswebg_nils hgiswebg_geodjango`

## Using Django commands. 
You can move data with Django commands. But this is very slow (Parcel table would take ~20 hours) if django is running far away from the DB, eg
with Django running locally and your DB running in the cloud.
1. Make sure the destination table is empty: `Delete from world_parcel` on the correct DB would work. Just be careful!
2. `LOCAL_DB=1 ./manage.py dumpdata world.Parcel > parcel.json.gz` : dump the data from local DB
3. `./manage.py loaddata parcel.json.gz` : upload data into central DB

We use the `LOCAL_DB=1` flag in our django app to select your local DB instance. 

Note: it's smart to inspect the json file to make sure no other STDOUT output
went into it.