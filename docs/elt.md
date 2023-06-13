
# ELT processes for ingestion of data

## References
* Mac Freeform diagram of ELT stages.
* Notion page tracking data sources and status: https://www.notion.so/turboprop/Turboprop-BOV-tech-511d75d42a0b4e068dd56dad5cb392cd
* 

## Overview

Pipeline stages:
1. Extract: External data source's data files or API calls. Data files will be in the deploy/data-files folder. 
API calls will typically go into ExternalApiData model (with caching mechanism).
2. Load: Data is loaded into a Raw<Data> model. The model name should be Raw<Geo><Datatype>, eg RawSantaAnaParcel. The model
should have a run_date field which is an auto_now=True date, and should have a 'geom' field if it's associated with
geometry. 
3. Transform: 

## Geography and data type names

We keep a consistent schema for data to record where it comes from and what kind of data it is. This schema is found in
elt/lib/types.py

## Input files

* Stored in local directory under `deploy/data-files/elt/` or in cloudflare R2 'parsnip-input-data' bucket
* Directory schema:
  * <geo>/[parcel|zoning|...]/<stage>/<date>.zip
  * eg. 'sd/parcel/0.shapefile/230215.zip'
  * copy files to R2 with `rclone copy <filename>.zip h3r2:parsnip-input-data/<geo>/shapes/<type>/`

* geo is
  * 'san' for San Diego
  * 'sta' for Santa Ana
  * 'orac' for Orange County
  * 'sf' for San Francisco
  * (cities have 3-letter abbreviations, matching airport codes if there's a prominent airport there. counties 
have 4-letter abbreviations ending with 'c')

## Running extraction

* Update files in directories you want to refresh. eg if you have updated SF parcel data, 
place a new sf/parcel/0.shapefile/<date>.zip

* `./manage.py elt <geo> <datatype>`

* If it's a new model type, the command will tell you to create new python files and create+run migrrations. Do that,
then run the command again. Make sure to add a run_date field to the model, since our ELT models all have that to 
track the data provenance by date. Don't set it to "auto_now". See extract_from_shapefile.py for example.
