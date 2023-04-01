## Setup steps

Recommended setup steps are to use:
* Mamba (a faster version of Conda) for managing system packages and environments. This is like a better 
version of 'brew' that supports multiple environments.
* Docker for running Postgres + PostGIS in a container. This is easier than running them directly on your system.

This section walks you through the steps:
### 1. Set up Mamba + system packages:
Mamba is a wrapper around Conda. It also installs Conda. 

Mamba creates a "base" environment that's used by default in any terminal. You can install packages you want
available to the whole system in that base environment.

To set it up:
- Install Mamba with the instructions [here](https://mamba.readthedocs.io/en/latest/installation.html). 
Download **mambaforge** from the link there for your computer architecture (eg. Mambaforge-MacOSX-arm64) for M1 Mac).
- If you open a terminal you should now see you're in the (base) environment from the prompt. If you `echo $PATH`, you 
should see the `mambaforge/bin` path at the beginning.
- You can install system-wide packages here, similar to how brew works, with `mamba install <package>`.
 
### 2. Docker image for Postgres:
This is the recommended way to run Postgres + Postgis on your local machine.
1. Get the Docker Desktop app (the M1 Mac app) from Docker.com and install it.
2. `docker pull ghcr.io/baosystems/postgis:14`  -- downloads the Postgis image. [Ref]( https://github.com/postgis/docker-postgis/issues/216#issuecomment-981824739).
3. In the Docker desktop UI, run the image. Make sure to set options:  
	- Env variable: `POSTGRES_PASSWORD` = password  (since it's a local DB, you can just use the word 'password')  
	- Port: 5432 to container port 5432
0. Run `psql -h localhost -U postgres` to test that you can connect to the DB. 
0. `createdb -h localhost -U postgres parsnip` -- postgres command to create the database called 'parsnip'

 
Running the Postgres Docker container does consume some battery power. You can stop the container when you're not 
using it. 



### 3. Setup Parsnip environment
From the parsnip directory:

- `mamba env create -f mamba-env.yml` -- creates the conda virual environment, downloading all the system packages 
you need.
- `mamba activate parsnip` -- activate the virtual environment we created. You need to do this whenever you 
open a new terminal window. It's the equivalent of activating a python virtual env, but for the whole system 
environnment.
- `cd frontend && yarn install && cd ..` -- install JS dependencies for frontend.
- `poetry install` -- install python dependencies for backend.
-  `./manage.py migrate` -- apply django migrations to the local DB
- `./manage.py createsuperuser` -- give yourself a superadmin account on django
 
Note: You'll periodically need to update frontend and backend dependencies as the code changes with `poetry install` and `yarn install` as 
above.
