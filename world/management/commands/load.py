from enum import Enum
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from world.models import WorldBorder, parcel_mapping, world_mapping, Parcel, ZoningBase, zoningbase_mapping, \
    BuildingOutlines, buildingoutlines_mapping
from django.core.management.base import BaseCommand, CommandError


class LoadModel(Enum):
    Parcel = 1
    Zoning = 2
    Buildings = 3

class Command(BaseCommand):
    help = 'Load data from a shape file into a Django model'

    def add_arguments(self, parser):
        parser.add_argument('model', choices=LoadModel.__members__)


    def handle(self, model, *args, **options):

        print (model)
        data_dir = Path(__file__).resolve().parent.parent.parent / 'data'
        if (model == "Parcel"):
            (fname, db_model, mapper) = ('PARCELS.shp', Parcel, parcel_mapping)
        elif (model == "Zoning"):
            (fname, db_model, mapper) = ('ZONING_BASE_SD/ZONING_BASE_SD.shp', ZoningBase, zoningbase_mapping)
        elif (model == "Buildings"):
            (fname, db_model, mapper) = ('BUILDING_OUTLINES/BUILDING_OUTLINES.shp', BuildingOutlines, buildingoutlines_mapping)

        # lm = LayerMapping(WorldBorder, shpfile, world_mapping, transform=False)
        lm = LayerMapping(db_model, data_dir / fname, mapper, transform=True)
        lm.save(strict=True, verbose=False, progress=True)
        self.stdout.write(self.style.SUCCESS('Finished writing data for model %s' % model))



