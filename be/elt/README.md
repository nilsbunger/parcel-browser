
# ELT processes for ingestion of data


## Input files

* Stored in cloudflare R2 'parsnip-input-data' bucket
* Directory schema:
  * <geo>/shapes/[parcel|zoning|...]/<date>.zip
  * eg. 'sd/shapes/parcel/230215.zip'
  * copy files to R2 with `rclone copy <filename>.zip h3r2:parsnip-input-data/<geo>/shapes/<type>/`

* geo is
  * 'san' for San Diego
  * 'sta' for Santa Ana
  * 'orac' for Orange County
  * (cities have 3-letter abbreviations, matching airport codes if there's a prominent airport there. counties have 4-letter abbreviations ending with 'c')

