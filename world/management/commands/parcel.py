import json
import pprint
import geopandas
import shapely
from django.core.serializers import serialize
from shapely.geometry import MultiLineString
from shapely.ops import triangulate
from lib.analyze_parcel_lib import analyze_one_parcel

from world.models import parcel_mapping, world_mapping, Parcel, ZoningBase, zoningbase_mapping, \
    BuildingOutlines, buildingoutlines_mapping
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Analyze a parcel'

    def add_arguments(self, parser):
        parser.add_argument('apn', nargs=1, type=str)
        parser.add_argument('--show-plot', '-p', action='store_true')
        parser.add_argument('--save-file', '-f', action='store_true')

    def handle(self, *args, **options):
        analyze_one_parcel(options['apn'][0],
                           show_plot=options['show_plot'],
                           save_file=options['save_file'])
        print("Done")

    def old_handle(self, *args, **options):
        pp = pprint.PrettyPrinter(indent=2)

        apn = '4302030800'

        # Get parcel and building info for this zone.
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        serialized_parcel = serialize('geojson', [parcel], geometry_field='geom', )
        serialized_buildings = serialize('geojson', buildings, geometry_field='geom', fields=('apn', 'geom',))
        parcel_data_frame = geopandas.GeoDataFrame.from_features(json.loads(serialized_parcel), crs="EPSG:4326")
        buildings_data_frame = geopandas.GeoDataFrame.from_features(json.loads(serialized_buildings), crs="EPSG:4326")
        parcel_in_utm = parcel_data_frame.to_crs(parcel_data_frame.estimate_utm_crs())
        buildings_in_utm = buildings_data_frame.to_crs(buildings_data_frame.estimate_utm_crs())

        print(pp.pprint(parcel.__dict__))
        lot_square_meters = parcel_in_utm.area
        print ("Lot: ", lot_square_meters)
        print ("buildings: ", buildings_in_utm.area)
        assert (len(parcel_in_utm.boundary) == 1)
        assert (len(buildings_in_utm.boundary) == 2)
        assert (len(parcel_in_utm.boundary[0].geoms) == 1)
        assert (len(buildings_in_utm.boundary[0].geoms) == 1)
        # TODO: Algorithm currently only takes first building. extend it to multiple buildings
        boundary_line_string = parcel_in_utm.boundary[0].geoms[0]
        building_line_string = buildings_in_utm.boundary[1].geoms[0]
        bounds = boundary_line_string.bounds
        boundary_line_string = shapely.affinity.translate(boundary_line_string, xoff=-bounds[0], yoff=-bounds[1])
        building_line_string = shapely.affinity.translate(building_line_string, xoff=-bounds[0], yoff=-bounds[1])
        pprint.pprint(list(boundary_line_string.coords))
        pprint.pprint(list(building_line_string.coords))
        triangles = triangulate (MultiLineString([boundary_line_string, building_line_string]))
        pprint.pprint([triangle.wkt for triangle in triangles])

        # r1_zones = ZoningBase.objects.filter(zone_name__istartswith='R-1')


        # print(pp.pprint(list(buildings).__dict__))
        self.stdout.write(self.style.SUCCESS('Finished running parcel'))



