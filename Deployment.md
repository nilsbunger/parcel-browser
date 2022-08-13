
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
2. OPTIONAL - `flyctl launch` -- if you don't already have a fly.toml and Dockerfile.
3. `flyctl volumes create pgdata 10` -- create a 10GB persistent volume
4. `flyctl secrets set POSTGRES_PASSWORD <secure_password>`
5. `flyctl deploy` . This *may* fail if the pgdata volume isn't set up one time. See the Dockerfile for more details.
### Administering the DB
* `flyctl proxy 15999:5432` -- create proxy from DB to local port 15999
* `psql postgres://postgres:<secure_password>@localhost:15999` -- run psql admin tool


## 2. Parsnip webapp
Parsnip's app tier runs `gunicorn` as a web server. It serves Django endpoints, React files, and static files (using the `whitenoise` package).

### Creating the web app
1. `cd deploy/webapp`
2. OPTIONAL - `flyctl launch` -- creates dockerfile and fly.toml if they don't already exist.
3. Set `flyctl secrets` for DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD. eg ``flyctl secrets set DB_HOST=<value>
    * DB_HOST=<hostname>.internal, eg parsnip-postgis-db.internal
    * DB_NAME=postgres
    * DB_USERNAME=postgres
    * DB_PASSWORD=<secure_password>
    * SECRET_KEY=...
  

### Updates to web app
... to be continued

