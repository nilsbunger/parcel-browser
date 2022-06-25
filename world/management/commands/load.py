# currently you run this with ./manage.py shell, then `from world import load` then `load.run()`
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from world.models import WorldBorder, parcel_mapping, world_mapping, Parcel, ZoningBase, zoningbase_mapping, \
    BuildingOutlines, buildingoutlines_mapping
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Load data from a shape file into a Django model'

    def add_arguments(self, parser):
        # parser.add_argument('poll_ids', nargs='+', type=int)
        pass


    def handle(self, *args, **options):
        # shpfile = Path(__file__).resolve().parent / 'data' / 'TM_WORLD_BORDERS-0.3.shp'
        # shpfile = Path(__file__).resolve().parent / 'data' / 'PARCELS.shp'
        # shpfile = Path(__file__).resolve().parent.parent.parent / 'data' / 'ZONING_BASE_SD' / 'ZONING_BASE_SD.shp'
        shpfile = Path(__file__).resolve().parent.parent.parent / 'data' / 'BUILDING_OUTLINES' / 'BUILDING_OUTLINES.shp'

        # lm = LayerMapping(WorldBorder, shpfile, world_mapping, transform=False)
        # lm = LayerMapping(Parcel, shpfile, parcel_mapping, transform=False)
        lm = LayerMapping(BuildingOutlines, shpfile, buildingoutlines_mapping, transform=True)
        lm.save(strict=True, verbose=False, progress=True)
        self.stdout.write(self.style.SUCCESS('Finished writing data'))



