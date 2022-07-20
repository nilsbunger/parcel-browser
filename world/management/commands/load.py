from enum import Enum
from pathlib import Path

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.utils import LayerMapping

from mygeo.util import eprint
from world.models import parcel_mapping, Parcel, ZoningBase, zoningbase_mapping, \
    BuildingOutlines, buildingoutlines_mapping, Topography, topography_mapping, TopographyLoads
from django.core.management.base import BaseCommand


class LoadModel(Enum):
    Parcel = 1
    Zoning = 2
    Buildings = 3
    Topography = 4


class Command(BaseCommand):
    help = 'Load data from a shape file into a Django model'

    def add_arguments(self, parser):
        parser.add_argument('model', choices=LoadModel.__members__)
        parser.add_argument('fname', nargs='?')

    def handle(self, model, fname=None, *args, **options):

        print(model)
        data_dir = Path(__file__).resolve().parent.parent.parent / 'data'
        if model == "Parcel":
            (fname, db_model, mapper) = ('PARCELS.shp', Parcel, parcel_mapping)
        elif model == "Zoning":
            (fname, db_model, mapper) = ('ZONING_BASE_SD.shp', ZoningBase, zoningbase_mapping)
        elif model == "Buildings":
            (fname, db_model, mapper) = ('BUILDING_OUTLINES.shp', BuildingOutlines, buildingoutlines_mapping)
        elif model == "Topography":
            (db_model, mapper) = (Topography, topography_mapping)
        else:
            eprint("Unknown model!")
            return
        # Do the actual load
        lm = LayerMapping(db_model, data_dir / fname, mapper, transform=True)
        lm.save(strict=True, verbose=False, progress=True)

        # Execute post-load tasks
        if model == "Topography":
            # record completion of topography load
            ds = DataSource(data_dir / fname)
            new_geom = GEOSGeometry(ds[0].extent.wkt, srid=2230)  # 2230 is NAD83, California Zone 6 code
            new_geom = new_geom.transform('EPSG:4326', clone=True)
            print("Recording topo extents in DB:", new_geom)
            loaded, was_created = TopographyLoads.objects.get_or_create(extents=new_geom)
            loaded.fname = fname
            loaded.save()

        self.stdout.write(self.style.SUCCESS('Finished writing data for model %s' % model))
