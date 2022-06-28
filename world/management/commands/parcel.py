import json
import pprint
from enum import Enum
from pathlib import Path

import geopandas
from django.contrib.gis.utils import LayerMapping
from django.core.serializers import serialize

from world.models import WorldBorder, parcel_mapping, world_mapping, Parcel, ZoningBase, zoningbase_mapping, \
    BuildingOutlines, buildingoutlines_mapping
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Analyze a parcel'

    def add_arguments(self, parser):
        # parser.add_argument('model', choices=LoadModel.__members__)
        pass

    def handle(self, *args, **options):
        pp = pprint.PrettyPrinter(indent=2)

        apn = '4302030800'

        # Get parcel and building info for this zone.
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        serialized_parcel = serialize('geojson', [parcel], geometry_field='geom', )
        serialized_buildings = serialize('geojson', buildings, geometry_field='geom', fields=('apn', 'geom',))
        parcel_data_frame = geopandas.GeoDataFrame.from_features(json.loads(serialized_parcel), crs="EPSG:4326")
        parcel_in_utm = parcel_data_frame.to_crs(parcel_data_frame.estimate_utm_crs())
        print(pp.pprint(parcel.__dict__))
        lot_square_meters = parcel_in_utm.area
        print ("Lot: ", lot_square_meters)

        r1_zones = ZoningBase.objects.filter(zone_name__istartswith='R-1')


        print(pp.pprint(list(buildings).__dict__))
        self.stdout.write(self.style.SUCCESS('Finished running parcel'))



