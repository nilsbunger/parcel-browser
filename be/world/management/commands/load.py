import subprocess
from enum import Enum
from pathlib import Path

import geopandas
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.utils import LayerMapping
from django.core.management import CommandParser
from django.core.management.base import BaseCommand
from elt.lib.types import Juri
from parsnip.util import eprint

from world.models import (
    BuildingOutlines,
    Parcel,
    Roads,
    Topography,
    TopographyLoads,
    TransitPriorityArea,
    ZoningBase,
)
from world.models.base_models import HousingSolutionArea
from world.models.base_models_mapping import (
    buildingoutlines_mapping,
    housingsolutionarea_mapping,
    parcel_mapping,
    roads_mapping,
    topography_mapping,
    transitpriorityarea_mapping,
    zoningbase_mapping,
)


class Cmd(Enum):
    db = 1
    tiles = 2


sf_schemas = {
    "shapefiles": {
        "ZoningDistricts": {
            "field_name_mappings": [
                ("zoning", "zoning"),
            ]
        },
        "ZoningHeightBulkDistricts": {"field_name_mappings": [("height", "height_name"), ("gen_hght", "height_val")]},
        "ZoningSpecialUseDistricts": {
            "field_name_mappings": [("name", "su_name"), ("url", "su_url")],
        },
        "Parcels": {
            "field_name_mappings": [
                ("from_addre", "from_addr"),
                ("to_address", "to_addr"),
                ("street_nam", "street"),
                ("street_typ", "suffix"),
                ("mapblklot", "mapblklot"),
                ("Geometry", "Geometry"),
            ],
            "group_by_field": "mapblklot,Geometry",
        },
        "Streets": {"field_name_mappings": [("name", "name"), ("type", "type"), ("Geometry", "Geometry")]},
    },
    "tilelayers": {
        "zoning": {"shapes": ["ZoningDistricts"]},
        "parcelroads": {"shapes": ["Parcels", "Roads"]},
    },
}
schemas = {
    "san_franciwsco": sf_schemas,
}


class Command(BaseCommand):
    help = "Load data from a shape file into a Django model"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "cmd",
            choices=Cmd.__members__,
            help="Command to run: db=load model into DB; tiles=generate + upload static tiles",
        )
        parser.add_argument(
            "geo",
            choices=Juri.__members__,
            help="Region (santa_ana, san_diego, san_francisco) to load data for",
        )
        # parser.add_argument("model", choices=LoadModel.__members__)
        parser.add_argument("fname", nargs="?")
        parser.add_argument(
            "--check-nulls",
            action="store_true",
            help="Don't load data, but print out fields which contain null values (and need "
            "blank=True null=True in the model).",
        )

    def handle(self, cmd, geo, fname, check_nulls, model=None, *args, **options):
        if cmd == "db":
            self.db_cmd(geo, model, fname, check_nulls)
        elif cmd == "tiles":
            self.tiles_cmd(geo, model, fname)
        else:
            eprint("Unknown command!")

    def tiles_cmd(self, geo, model, fname):
        from parsnip import settings

        dir = settings.BASE_DIR / "deploy" / "data-files" / geo
        shapefiles = sorted(Path(dir).rglob("*.shp"))
        # Turn shape-file into line-delimited GeoJSON (ldgeojson) w/ translation to lat/long. Convert the shapefiles
        # 1:1 into GeoJSON files. Consolidation happens in later step
        for shapefile in shapefiles:  # TODO: Temporarily just get one file (the zoning file)
            eprint(f"Processing {shapefile}")
            shape_name = shapefile.parts[-2]  # use leaf directory name (e.g. "ZoningDistrict") as the file name
            outfile = dir / "out" / f"{shape_name}.geojson.ld"
            shape_cfg = schemas["sf"]["shapefiles"][shape_name]
            ogrsql = "'SELECT " + ",".join(
                [f"{mapping[0]} AS {mapping[1]}" for mapping in shape_cfg["field_name_mappings"]]
            )
            ogrsql += f' FROM "{shapefile.stem}"'
            if "group_by_field" in shape_cfg:
                ogrsql += f' GROUP BY {shape_cfg["group_by_field"]}'
            ogrsql += "'"
            ogr2ogr_cmd = (
                f"ogr2ogr -dim 2 -t_srs 'EPSG:4326' -f 'GeoJSON' -dialect sqlite -sql {ogrsql} {outfile} {shapefile}"
            )
            eprint(f"Running: {ogr2ogr_cmd}")
            process_result = subprocess.run(ogr2ogr_cmd, check=True, shell=True)
            assert process_result.returncode == 0, f"ogr2ogr failed with return code {process_result.returncode}"

        for layername, layercfg in schemas[geo]["tilelayers"].items():
            eprint(f"Building tile layer: {layername}")
            shapefiles = [str(dir / "out" / f"{shape}.geojson.ld") for shape in layercfg["shapes"]]

            # Now make the tilelayer from the GeoJSON file(s). Multiple shapefiles get combined here into one MVTile layer.
            process_result2 = subprocess.run(
                f"tippecanoe --no-feature-limit --no-tile-size-limit --minimum-zoom=16 --maximum-zoom=16 "
                f"--read-parallel -l {layername} --no-tile-compression {' '.join(shapefiles)} "
                f"--output-to-directory {dir / 'out' / layername}",
                check=True,
                shell=True,
            )
            assert process_result2.returncode == 0, f"tippecanoe failed with return code {process_result2.returncode}"
            print(process_result)
            # schema = self.schemas[geo][shape_name]
            # with fiona.open(shapefile) as src:
            #     dest = tempfile.TemporaryFile()
            #     with fiona.open(dir / "out" / (shape_name + ".ldgeojson"), "w", driver="GeoJSON", crs="EPSG:4326",
            #                     schema=schema) as dst:
            #         for f in src:
            #             dst.write(f)
            #     print("DONE")

        print(dir)
        pass

    def db_cmd(self, geo, model=None, fname=None, *args, **options):
        raise AssertionError("Update for regions, new paths, and automating file discovery")
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
            (fname, db_model, mapper) = ("Roads_All/Roads_All.shp", Roads, roads_mapping)
        elif model == "TPA":
            (fname, db_model, mapper) = (
                "TRANSIT_PRIORITY_AREA.shp",
                TransitPriorityArea,
                transitpriorityarea_mapping,
            )
        elif model == "HousingSolutionArea":
            (fname, db_model, mapper) = (
                "HOUSING_SOLUTION_AREAS/HOUSING_SOLUTION_AREAS.shp",
                HousingSolutionArea,
                housingsolutionarea_mapping,
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
            new_geom = GEOSGeometry(ds[0].extent.wkt, srid=2230)  # 2230 is NAD83, California Zone 6 code
            new_geom = new_geom.transform("EPSG:4326", clone=True)
            print("Recording topo extents in DB:", new_geom)
            loaded, was_created = TopographyLoads.objects.using(using_db).get_or_create(extents=new_geom)
            loaded.fname = fname
            loaded.save(using=using_db)

        self.stdout.write(self.style.SUCCESS("Finished writing data for model %s" % model))
