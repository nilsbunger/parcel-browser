import json
import os, sys

from django.contrib.gis.db.models.functions import Intersection
from django.core.serializers import serialize

PROJECTPATH = os.environ['PWD']
print (PROJECTPATH)
sys.path.insert(0, PROJECTPATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygeo.settings")
os.environ.setdefault("DJANGO_PROJECT", "mygeo")
os.environ.setdefault("LOCAL_DB", "1")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.chdir(PROJECTPATH)
import django
django.setup()
from lib.parcel_lib import get_buildings, models_to_utm_gdf, get_parcel
from world.models import Topography


from shapely.geometry import Point, Polygon, box, MultiPolygon, MultiLineString

from django.contrib.gis import geos
import geopandas
from shapely import wkt

parcel_with_hill = '3185302100'
parcel = get_parcel(parcel_with_hill)
buildings = get_buildings(parcel)
# Get the topography objects intersecting with the parcel under consideration. We make the DB calculate the
# intersection. It's a raw query because Django won't let us overwrite a model field (topography.geom) with a
# calculated field (the geometry intersection). The query is equivalent to the commented-out normal Django query below.
topos = Topography.objects.raw(
    'Select id,elev,ltype,index_field,shape_length,ST_Intersection("geom", ST_GeomFromEWKB(%s))::bytea AS "geom" '
    'from world_topography WHERE ST_Intersects("geom", ST_GeomFromEWKB(%s))',
    [parcel.geom.ewkb, parcel.geom.ewkb]
)
# topos = Topography.objects.filter(    # this is the query we want, but Django won't let us do.
#     geom__intersects=parcel.geom).annotate(geom=Intersection('geom', parcel.geom)).defer('geom')

# Originally the buidings_to_utm_gdf code,
topos_df = models_to_utm_gdf(topos)
buildings_df = models_to_utm_gdf(buildings)
parcel_df = models_to_utm_gdf([parcel])
parcel_df.geometry = parcel_df.geometry.boundary

(xmin,ymin,xmax,ymax) = parcel_df.total_bounds.tolist()

# Try to find the elevation from the contours
pt = (xmax-xmin, ymax-ymin)

# Translating a single polygon into a shapely shape:
# shapely_shape = wkt.loads(topos[0].geom.wkt)

p1 = parcel_df.plot()
buildings_df.plot(ax=p1, )

p2 = topos_df.plot(ax=p1)

# geopandas.GeoSeries([parcel, buildings, topos]).plot()
