

# Creating a static vector tile set, hostable by R2.

What this process does is translate shapefiles (which we get from the cities) into vector tiles. Vector tiles are 
the format consumed by our mapping viewers.

References:
https://geovation.github.io/build-your-own-static-vector-tile-pipeline
https://geovation.github.io/tiler
https://docs.mapbox.com/mapbox-tiling-service/guides/tileset-sources/#line-delimited-geojson
https://github.com/dwtkns/gdal-cheat-sheet -- lots of ogr2ogr command examples

# Tools:

In virtualenv:
* Fiona CLI -- `pip install fiona`. This is the python API to OGR
* Mapbox Tilesets -- `pip install mapbox-tilesets`  -- CLI for interacting with the Mapbox Tilesets API

Other:

* brew install tippecanoe rclone
* QGIS app for viewing shapefiles and vector tiles

# Sequence:

We've done this with the parcels and roads shapefiles first, as they are the slowest to
load and most detailed. It can be extended to zoning and other layers, though you need
to filter those similar to the TileData view in world/views.py

* Look at the shapefile, understand its fields and coordinate system.
`fio info --indent 2 <shpfile>` gives the data schema AND
* Browse shapefile with QGIS app and see all the attributes (Layer / Open Attribute Table)

* Turn shape-file into line-delimited GeoJSON (ldgeojson) w/ translation to lat/long
  (EPSG4326)

`ogr2ogr -dim 2 -f 'GeoJSON' -sql "SELECT RD30FULL as rd30full, ROADSEGID as roadsegid, RIGHTWAY as rightway, ABLOADDR as abloaddr, ABHIADDR as abhiaddr from Roads_all" -t_srs 'EPSG:4326' /tmp/roads.ldgeojson.ld ../Roads_all/Roads_all.shp`
`ogr2ogr -dim 2 -f 'GeoJSON' -sql "SELECT APN as apn from PARCELS" -t_srs 'EPSG:4326' /tmp/parcel.ldgeojson.ld ../PARCELS/PARCELS.shp`

     - Output file is about 2x larger than input file.
     - We select attributes here to change them to lowercase. The next step can just
       include all the attributes.
     - Previously tried `fio cat ../PARCELS/PARCELS.shp > parcels.ldgeojson.ld` but
       fiona is slower AND we need the coordinate system transform.

* Generate tiles

`tippecanoe --no-feature-limit --no-tile-size-limit --minimum-zoom=16 --maximum-zoom=16 --read-parallel -l parcelroads --no-tile-compression parcel.ldgeojson.ld roads.ldgeojson.ld  --output-to-directory "/tmp/parcel-roads"`
    - This example combines roads and parcels geojson
    - Includes all feature attributes since the ones we want were selected in previous
      step
    - Don't support higher than 16 zoom because that implies 1cm resolution, file size
      blows up.
    - See https://geovation.github.io/build-your-own-static-vector-tile-pipeline for

* Upload tiles to R2 bucket:
`rclone --progress copy /tmp/parcel-roads/ h3cloudflarer2:mvt/sd/parcel-roads/`
    - you need to have rclone configured for this, including a cloudflare api key.


# Future work
* The served tiles have no cache-control headers. Would be good to add them. If we need
  to update the tiles, we should version the paths (or use a query string to cache
  bust?)
* The R2 bucket is public access at the moment. We should change that to a mechanism
  requiring auth at some point.

