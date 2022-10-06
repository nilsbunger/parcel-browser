# Parsnip
Home3 application for evaluating parcels for upzoning.

# Setup steps
This is currently working on a Mac with M1 processor. Will need tweaks for other environments.

`brew install gdal` - translator library for raster and vector geospatial data formats

`brew install python3` - use python 3.8 or newer

`pip3 install geopandas` - adds support for geographic data to pandas objects


From the project directory:
`python3 -m venv ./venv` to create a venv ([ref](https://docs.python.org/3/library/venv.html))

`source ./venv/bin/activate` activates the virtual env. You need to do this in any terminal window where you're running Django, Jupyter Lab, or related tools.

`cp .env.example .env` -- create your .env file.

# Install or update dependencies

`pip install -r requirements.txt`

`cd frontend && yarn install` -- install dependencies for frontned

Note: You'll periodically need to update python and yarn dependencies as the code changes.

# Set up a local database

You'll need a local DB or access to a cloud DB to run the service. A local DB is best for dev, because the latencies from app server to DB make things very slow. It's easy to switch between them, so you might as well set up one locally. 

1. `brew install postgres`

2. `brew install postgis` - PostgreSQL extension for geometry types and geospatial functions. Installs it with the protobuf support compiled in.

3. `brew services start postgres` -- Run the Postgres server as a service in the background

4. `createdb geodjango` -- postgres command to create the database

5. `./manage.py migrate` -- apply django migrations to the local DB

6. `./manage.py createsuperuser` -- give yourself a superadmin account on django

The above is mostly a one-time setup. 

# Running in dev
You'll need to run frontend and backend servers:

`cd frontend && yarn dev` -- start frontend (parcel) dev server

Now start the Django server (remember to start the virtual env if you didn't already):
`./manage.py runserver`

Browse to http://localhost:8000/map or http://localhost:8000/admin . 

If you haven't loaded any data, you should see an OpenStreetMap map at /map, but you won't see parcels.

# System architecture

The app is a Django application at its core.

The major components of the system are:

- DB: Postgres with PostGIS
- App server:
    - Django with GeoDjango library (built-in),
    - Shapely (geometry manipulation)
    - GeoPandas (GeoDataFrame and GeoSeries), which includes pandas for data analysis and shapely for geometry manipulation.
- Front end:
    - OpenLayers map viewer (see, for example, map.ts)

When you're working on the code, you'll want the docs open for Shapely, GeoPandas, and Django querysets and GeoDjango. You can google for all of them.


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

1. Download Parcels, Building_outlines (under MISCELLANEOUS), Zoning_base_sd, Topos_2014_2Ft_PowayLaMesa ZIP, and Topos_2014_2Ft_LaJolla.gdb files from https://www.sangis.org/ . You'll need a free account. Get the associated PDF files as well, as they are useful in describing what the data means.
2. Unzip and put all files in world/data/  
3. Load the shape files into the DB. NOTE: Use LOCAL_DB=0 or LOCAL_DB=1 to specify cloud or local DB to load.
`./manage.py load Zoning`

`./manage.py load Parcel`

`./manage.py load Buildings`

`./manage.py load Topography Topo_2014_2Ft_PowayLaMesa.gdb`

`./manage.py load Topography Topo_2014_2Ft_LaJolla.gdb`

`./manage.py load Roads`

`./manage.py load HousingSolutionArea'

~~4. Run ETL jobs as necessary, eg:
`./manage.py dataprep labels all`: (re-)generate labels for zones


# Creating new GIS data tables from a shape file

If you're adding a new class of GIS data based on a shape files, there are some tools to make it easier.

1. Try inspecting your new shape file:
- `ogrinfo -so <shapefile>.shp` -- shows layers  
- `ogrinfo -so <shapefile>.shp <layername>` -- examines a layer

2. Generate Django models and mapping automatically:
- Use `./manage.py ogrinspect <shapefile> <ModelName> --srid=4326 --mapping --multi` 
- Add the generated model and mapping to models.py.
- Check which fields are nullable by running `load.py MODEL_NAME --check-nulls`. This will print out which fields have null in them. You'll need to add `blank=True null=True` to the respective models.py fields.
3. Perform Django migrations
- `./manage.py makemigrations`  
- `./manage.py migrate`
4. Update the `load.py` management command to load this new type of shape file
4. Execute the load management command as per Importing Data section above.

See also the django GIS tutorial [here](https://docs.djangoproject.com/en/4.0/ref/contrib/gis/tutorial/#try-ogrinspect), which shows using ogrinspect this way 

You'll need to manipulate the generated models in a few ways:
1. Load still might fail during load if any data field is empty. You'll need to add `blank=True null=True` to the models.py field that can be null, and make and run another migration. 
- **TIP:** To make things easier, you can set up a custom start point for the data to save, so you don't have to always run `load.py` from the start again. Simply add `fid_range=(START,END)` as an argument to `lm.save()`. For reference: https://docs.djangoproject.com/en/4.0/ref/contrib/gis/layermapping/
3. There are no indexes or foreign keys in this model. Depending on how you intend to use it, you should consider adding those. They can be added later, of course.

# Scripts

We're working on several scripts that run outside a Django environment. This is in flux, but here's one you can try:
`./manage.py runscript richard_parcel_test`
This comes from the scripts/ directory, and you can create more files there.

# Using a cloud DB instead of local DB

The Django app can be pointed at a cloud DB easily. You just need to set the env variable LOCAL_DB=0. You can set that in your own .env file, or add it to each command line, or add it to the shell environment. At that point, all Django commands (like `migrate`, `runserver`, and our custom scripts) will access the cloud DB.


# Copying data from one DB to another

You don't need this section for initial setup. But once you have data set up in one DB, and want to set up a remote DB, this info can come in handy. It's much faster to move large tables (like the table from the Parcel.shp file) using these instructions, compared to using Django management commands. 

Here are some steps for copying data between databases:

## Moving data using SQL clients
Using a SQL client to create and move a table is pretty fast. Even the 3GB Parcel
table can be exported and imported in a few minutes.

Here's an example of copying from your local DB to our cloud DB:
1. Make sure the destination table is empty: `Delete from world_*` on the correct DB would work. Just be careful!
2. `pg_dump -a -t 'world_parcel' geodjango | gzip > world_parcel_dump.sql.gz` where 'geodjango' is the local DB name and world_parcel is the DB table to export
4. Optional - Send the file to the remote machine to be close to the DB. Example for AcuGIS server:
    `scp -i id_rsa ../world_dump.sql.gz hgiswebg@us14.acugis-dns.com:~`
6. Load the file into the new DB. Example for AcuGIS server:
    `gunzip -c world_parcel_dump.sql.gz | psql -U hgiswebg_nils hgiswebg_geodjango`

## Moving data using Django commands. 
You can move data with Django commands. But this is very slow (Parcel table would take ~20 hours) if django is running far away from the DB, eg
with Django running locally and your DB running in the cloud.
1. Make sure the destination table is empty: `Delete from world_parcel` on the correct DB would work. Just be careful!
2. `LOCAL_DB=1 ./manage.py dumpdata world.Parcel > parcel.json.gz` : dump the data from local DB
3. `./manage.py loaddata parcel.json.gz` : upload data into central DB

We use the `LOCAL_DB=1` flag in our django app to select your local DB instance. 

Note: it's smart to inspect the json file to make sure no other STDOUT output
went into it.
