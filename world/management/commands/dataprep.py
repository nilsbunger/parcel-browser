from enum import Enum
import django
from django.contrib.gis.db.models import Extent

from lib.crs_lib import get_utm_crs
from lib.topo_lib import (
    calculate_parcel_slopes,
    calculate_parcel_slopes_mp,
    check_topos_for_parcels,
)
from django.core.management.base import BaseCommand

from world.models import Parcel


class Neighborhood(Enum):
    # Mira Mesa neighborhood of San Diego
    Miramesa = -117.17987773162996, 32.930825570911985, -117.12513392170659, 32.894946222075184
    MiramesaSmall = (-117.135284737197, 32.905422120627904, -117.13317320050437, 32.90428935023001)

    # Special "neighborhood" - compute full extents of all parcels
    all = tuple()

    # ... add more neighborhoods here


class Command(BaseCommand):
    help = "Run data preparation tasks on loaded data prior to analysis"

    def add_arguments(self, parser):
        parser.add_argument("hood", choices=Neighborhood.__members__)
        parser.add_argument(
            "--check",
            "-c",
            action="store_true",
            help="Check data instead of actually running all prep",
        )

    def handle(self, hood, *args, **options):
        # Parcel Slopes calculation - depends on Analyzed Parcels and Topography to be loaded.
        # tracemalloc.start()

        if hood == "all":
            print(f"Working with ALL parcels.")
            print("Finding bounding box...")
            bounding_box_tuple = Parcel.objects.aggregate(foobar=Extent("geom"))["foobar"]
            print(f"Bounding box is {bounding_box_tuple}")
        else:
            print(f"Working with parcels in {hood} neighborhood")
            bounding_box_tuple = Neighborhood[hood].value
        bounding_box = django.contrib.gis.geos.Polygon.from_bbox(bounding_box_tuple)
        sd_utm_crs = get_utm_crs()
        if options["check"]:
            check_topos_for_parcels(bounding_box)
        else:
            print(f"Calculating slopes for parcels in {hood} neighbordhood(s)")

            # Put behind feature flag in case parallel breaks
            if True:
                calculate_parcel_slopes_mp(bounding_box, sd_utm_crs)
            else:
                calculate_parcel_slopes(bounding_box, sd_utm_crs)
            self.stdout.write(
                self.style.SUCCESS(f"Finished calculating parcel slopes for neighborhood {hood}")
            )
