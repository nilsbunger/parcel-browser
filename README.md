# Parsnip
Home3 application for evaluating parcels for upzoning.

# Setup

Setup Django, Postgres, and frontend using these steps:

* [Setup steps](docs/setup.md) including Mamba environment setup.
* [Old brew-based (deprecated) setup steps](docs/archived-brew-setup.md)

# Running in dev
When you've completed setup, you're ready to run. You need to run frontend and backend servers:

1. Make sure the Mamba environment is activated:

   `mamba activate parsnip`

0. Start the frontend server:
   
   `cd fe && yarn dev` -- start frontend dev server. This will watch for changes and rebuild the JS bundle.

0. Start the Django server:
    
   `cd be && ./manage.py runserver`

Browse to http://localhost:8000/map or http://localhost:8000/admin and see if things work.

If you haven't loaded any data, you should see an OpenStreetMap map at /map, but you won't see parcels.

# Management commands

## Finding management commands
Run `./manage.py` with no options to see all the managemenet commands available, organized by Django 'app'.

This lists all commands defined by all Django apps in the project:
* built-in apps (eg "django", "auth", ...) 
* third party apps (eg "django_extensions", "silk", ...) 
* our apps (eg. "world", "co", "userflows", ...)

## Existing management commands

In `world/management/commands/` and `co/management/commands` you'll find our custom command-line commands for
doing ETL and various other processing. 

Some examples:
* `LOCAL_DB=0 ./manage.py scrape --fetch --no-cache` -- daily scraping run. 
This requires Wireguard tunnel to cloud postgres to be running
* `./manage.py` -- list all management commands. The commmands we created are in `world` and `co` apps.

## Custom management commands

Custom management commands are the easiest way to write python code that interacts with our database and isn't a web app.

You can add a new file in this directory and <app>/management/comands and it magically become a Django mgmt command.
It can be run with `./manage.py <command> <params>`, where <command> is the name of the file you created.{

# Testing

## Running tests

We use pytest for testing. Run tests with:
* `poetry run pytest -s` to run all tests , OR
* `poetry run pytest -s -k <match>` to run any class or test matching <match>

## Test files

Any file that starts with test*.py is picked up by pytest. See examples in `userflows/tests.py` and 
`lib/co/test_co_eligibility.py` for inspiration.

## Populating the DB for tests

The test DB is empty by default. 
You can add more data by following the example. 

You can get data from the existing DB by dumping it:

`./manage.py dumpdata <app.model> --pks pk1,pk2,pk3 --format yaml`

We've extended the dumpdata command to support APNs. Any model with an APN field can be looked up by APN, 
using the `--apns` option. For example:

`./manage.py dumpdata world.Parcel --apns 4151721900,4472421600,5571022400 --format yaml`

You can take that output and load it as a fixture. See `conftest.py` to either append to the existing fixtures 
or create a new one and load it in that file.

# Code quality and style

Tools we use, and how to run them. You should run these before committing code:
* Python:
  * `black .` : autoformat python code (and write changes to files)
  * `ruff check .`: Lint python code
* Typescript:
  * `yarn lint`: Run eslint
  * `yarn prettier`: autoformat typescript code (and write changes to files)

# Simulate the production environment locallly

You don't usually need to do this, but if you need to debug an environment more similar to production,
you can run the app in production mode as follows:

1. Build frontend files: 
`cd fe && yarn build && cd ..`

2. Collect static files:
`cd be && ./manage.py collectstatic -v3 --noinput`

3. Serve with similar command line as in production:
`DJANGO_ENV=production LOCAL_DB=1 DJANGO_SECRET_KEY=12345 poetry run gunicorn --bin :8080 --workers 3 parsnip.wsgi:application`

It is possible to go even higher fidelity, by running in a docker container.

=======
# Using poetry

We use poetry as our python package manager. It installs packages and manages your virtual environment.

A few useful commands:
* `poetry run <command>` : run a single command in the virtual environment
(alternative to `poetry shell` for a single command) 
* `poetry add <package>` : add a package to the project (and update pyproject.toml and poetry.lock)
* `poetry add --group dev <package>` : add a development-only package
* `poetry env info` : show info about the virtual environment
* `poetry show --tree`: show the dependency tree
* `poetry install`: install dependencies based on pyproject.toml and poetry.lock into a venv.
* `poetry shell` : start a shell in the virtual environment. That shell will give you
the right python version and all the packages installed. NOTE: I think this is not necessary with the mamba-based environment.

# System architecture

## Components
The app is a Django application at its core.

The major components of the system are:

- DB: Postgres with PostGIS
- App server:
    - Django with GeoDjango library (built-in),
    - Shapely (geometry manipulation)
    - GeoPandas (GeoDataFrame and GeoSeries), which includes pandas for data analysis and shapely for geometry manipulation.
- Cron server:
  - Periodic jobs are run using supercron. A separate instance of the django app 
server is instantiated with supercron.
- Front end: (deployed in app server)
  - React using Parcel for bundling.
  - Deck.gl (for mapping using webgl)
  - Some older pages using Shapely and react-table (react-table is kind of a nightmare)


## Production and staging environments

We have separate staging and production environments, at stage-app.turboprop.ai and app.turboprop.ai. Each environment
has its own Django server and Postgres+PostGIS DB server running as a set of fly.io VMs.

Both the staging and prod apps are proxied through the Cloudflare CDN. Cloudflare's 
TLS mode is set to "Full" for each domain so we have connection security between Cloudflare and the client,
and between Cloudflare and our Django app server.

# React and static files
See [static-files.md](docs/static-files.md) to learn how React and static files are served in dev and prod.


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

`./manage.py load HousingSolutionArea`

4. Run ETL jobs as necessary, eg:
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

# Using the fly.io prod DB instead of local DB

The local Django app can be pointed at our fly.io DB:
1. Set up Wireguard tunnel running from your machine to cloud DB at fly.io. Fly.io has instructions on this.
2. From deploy/postgres directory: `fly proxy 15999:5432` to put the production DB at local port 15999
3. Add LOCAL_DB=0 before any `./manage.py` command to use the cloud DB instead of local DB.

We mostly use this config for running the daily listings scrape + analysis.

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

# Github Actions

We use Github Actions to run our tests and deploy to fly.io. 
The config is in `.github/workflows`.

Github Action's runner images are found in [this repo](https://github.com/actions/runner-images). We currently use
the Ubuntu 20.04 image which includes Postgres 14.6.

[This blog post](https://blog.healthchecks.io/2020/11/using-github-actions-to-run-django-tests/) has an
example of a Github Action configuration with Django and Postgres. 



# Hardcore debugging

Sometimes we get segmentation faults because of stupid issues with shapely libraries.
An example of how to debug that:
* ` lldb --arch arm64 python ./manage.py scrape -- --parcel 3091021200 --verbose -v3 --dry-run`
* Inside lldb, run `run` to start the program, and `cont` when it pauses
* When it crashes, run `bt` to get a backtrace


# Future work

* Editable layers in the map, eg to define a housing unit. Use something like https://github.com/uber/nebula.gl, which works with deck.gl
