from enum import Enum
import django

from lib.crs_lib import get_utm_crs
from lib.topo_lib import calculate_parcel_slopes
from django.core.management.base import BaseCommand


class Neighborhood(Enum):
    # Mira Mesa neighborhood of San Diego
    Miramesa = (-117.17987773162996, 32.930825570911985, -117.12513392170659, 32.894946222075184),
    # ... add more neighborhoods here


class Command(BaseCommand):
    help = 'Run data preparation tasks on loaded data prior to analysis'

    def add_arguments(self, parser):
        parser.add_argument('hood', choices=Neighborhood.__members__)

    def handle(self, hood, *args, **options):
        # Parcel Slopes calculation - depends on Analyzed Parcels and Topography to be loaded.
        print(f'Calculating slopes for parcels in {hood} neighborhood')
        bounding_box_tuple = Neighborhood[hood].value
        sd_utm_crs = get_utm_crs()
        bounding_box = django.contrib.gis.geos.Polygon.from_bbox(*bounding_box_tuple)

        calculate_parcel_slopes(bounding_box, sd_utm_crs)

        self.stdout.write(self.style.SUCCESS(f'Finished calculating parcel slopes for neighborhood {hood}'))
