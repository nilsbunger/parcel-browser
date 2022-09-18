from enum import Enum
from pathlib import Path
import geopandas

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.utils import LayerMapping

from mygeo.util import eprint
from world.models import (
    Parcel,
    ZoningBase,
    BuildingOutlines,
    Topography,
    TopographyLoads,
    Roads,
    TransitPriorityArea,
)
from django.core.management.base import BaseCommand

from world.models.base_models_mapping import (
    buildingoutlines_mapping,
    parcel_mapping,
    roads_mapping,
    topography_mapping,
    transitpriorityarea_mapping,
    zoningbase_mapping,
)


class LoadModel(Enum):
    Parcel = 1
    Zoning = 2
    Buildings = 3
    Topography = 4
    Roads = 5
    TPA = 6


class Command(BaseCommand):
    help = "Load data from a shape file into a Django model"

    def add_arguments(self, parser):
        parser.add_argument("model", choices=LoadModel.__members__)
        parser.add_argument("fname", nargs="?")
        parser.add_argument(
            "--check-nulls",
            action="store_true",
            help="Don't load data, but print out fields which contain null values (and need "
            "blank=True null=True in the model).",
        )

    def handle(self, model, fname=None, *args, **options):

        print(model)
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        if model == "Parcel":
            (fname, db_model, mapper) = ("PARCELS.shp", Parcel, parcel_mapping)
        elif model == "Zoning":
            (fname, db_model, mapper) = ("ZONING_BASE_SD.shp", ZoningBase, zoningbase_mapping)
        elif model == "Buildings":
            (fname, db_model, mapper) = (
                "BUILDING_OUTLINES.shp",
                BuildingOutlines,
                buildingoutlines_mapping,
            )
        elif model == "Topography":
            (db_model, mapper) = (Topography, topography_mapping)
        elif model == "Roads":
            (fname, db_model, mapper) = ("Roads_All/ROADS_ALL.shp", Roads, roads_mapping)
        elif model == "TPA":
            (fname, db_model, mapper) = (
                "TRANSIT_PRIORITY_AREA.shp",
                TransitPriorityArea,
                transitpriorityarea_mapping,
            )
        else:
            eprint("Unknown model!")
            return

        if options["check_nulls"]:
            """Helps check for which fields have null values. When creating new models for
            the first time, run this, and then add "blank=True, null=True" to the models.
            Works by loading the shapefile into a data frame, and then checking which columns
            contain null values.
            """
            print("Checking nullable fields...")
            df = geopandas.read_file(data_dir / fname)
            nullable_fields = [c for c in df if df[c].isnull().values.any()]
            print("Nullable fields:", nullable_fields)
            return

        # Do the actual load

        # We used to only support topos in the local DB; now we use whatever the LOCAL_DB= env variable says
        # using_db = "local_db" if db_model == Topography else "default"
        using_db = "default"
        lm = LayerMapping(db_model, data_dir / fname, mapper, transform=True, using=using_db)

        lm.save(strict=True, verbose=False, progress=True)

        # Execute post-load tasks
        if model == "Topography":
            # record completion of topography load
            ds = DataSource(data_dir / fname)
            new_geom = GEOSGeometry(
                ds[0].extent.wkt, srid=2230
            )  # 2230 is NAD83, California Zone 6 code
            new_geom = new_geom.transform("EPSG:4326", clone=True)
            print("Recording topo extents in DB:", new_geom)
            loaded, was_created = TopographyLoads.objects.using(using_db).get_or_create(
                extents=new_geom
            )
            loaded.fname = fname
            loaded.save(using=using_db)

        self.stdout.write(self.style.SUCCESS("Finished writing data for model %s" % model))
