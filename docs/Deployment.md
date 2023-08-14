
# Fly.io deployment

1. Get fly.io account credentials.
You need to download `flyctl` and create an account as described [here](https://fly.io/docs/getting-started/installing-flyctl/).

Get added to the Home3 org on fly.io by asking Nils or Marcio.

# VMs
## 1. Postgres DB with postgis extension
We run Postgres using the Postgres Docker image with PostGIS extensions. You can find the Dockerfile and related stuff in `deploy/postgres/`. The instance has an attached persistent volume in fly.io where the data is stored.
### Creating the DB
It's unlikely we will need to recreate the DB, but if we did, the steps are:
1. `cd deploy/postgres`
2. IF NEEDED - `flyctl launch` -- if you don't already have a fly.toml and Dockerfile.
3. `flyctl volumes create pgdata 10` -- create a 10GB persistent volume
4. `flyctl secrets set POSTGRES_PASSWORD <secure_password>`
5. `flyctl deploy` . This *may* fail if the pgdata volume isn't set up one time. See the Dockerfile for more details.
### Administering the DB
* `cd deploy/postgres && flyctl proxy 15999:5432` -- create proxy from DB to local port 15999
* `psql postgres://postgres:<secure_password>@localhost:15999` -- run psql admin tool. You can also connect DBeaver or another GUI tool with these credentials, as long as the proxy is running.

## 2. Parsnip webapp
Parsnip's app tier runs `gunicorn` as a web server. It serves Django endpoints, React files, and static files (using the `whitenoise` package).

### Creating the web app
1. Start from app root directory.
2. IF NEEDED - `flyctl launch` -- creates dockerfile and fly.toml if they don't already exist.
3. Set `flyctl secrets` for DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD. eg ``flyctl secrets set DB_HOST=<value>
    * DB_HOST=<hostname>.internal, eg parsnip-postgis-db.internal
    * DB_NAME=postgres
    * DB_USERNAME=postgres
    * DB_PASSWORD=<secure_password>
    * SECRET_KEY=...
4. run `flyctl deploy`. This should run a migration AND deploy your app if you're lucky :)

### Deploy to staging

1. `fly deploy` from parsnip directory. 

This deploys to https://stage-app.turboprop.ai

### Deploy to production

1. `fly deploy -c fly.prod.toml` from parsnip directory.

This deploys to https://app.turboprop.ai


## Uploading data

We have a lot of parcel data that needs to be in the app to work. Follow these steps to get it in place
### 1. Establish VPN connectivity
Follow the steps [here](https://fly.io/docs/reference/private-networking/#private-network-vpn) :
   1. Install the Wireguard app on your computer
   2. `fly wireguard create home3 <region>` and have it save a .conf file. 
   3. Load the .conf file into Wireguard and enable it.
   4. Run `fly ssh issue --agent` 
   5. Now `dig +noall +answer _apps.internal txt` should show you all apps you have a connection to.
   6. You can now directly ssh or scp to them. eg: `ssh root@parsnip.internal` and `scp <filename> root@parsnip.internal:/app/`
       Note: for this to work, the Docker container needs to have openssh-client installed via apt-get.

### 2. Upload data
A lot of our data are things like parcel info etc, which we only have to refresh rarely if ever. Upload those first as follows:
   1. `pg_dump -a -t world_parcel -t world_buildingoutlines -t world_zoningbase -t world_transitpriorityarea -t world_roads | gzip > world_slowmoving.sql.gz`
   2. `scp world_slowmoving.sql.gz root@parsnip.internal:/app`
   3. In the Docker container, `gunzip -c world_slowmoving.sql.gz | psql postgresql://postgres:<passwd>@parsnip-postgis-db.internal:5432`
Now, upload the nightly data needed for property listings.
   1. `pg_dump -a -t world_propertylisting | zip > world_proplistings.sql.gz`
   2. `scp world_proplistings.sql.gz root@parsnip.internal:/app`
   3. In the Docker container, `gunzip -c world_proplistings.sql.gz | psql postgresql://postgres:<passwd>@parsnip-postgis-db.internal:5432`
