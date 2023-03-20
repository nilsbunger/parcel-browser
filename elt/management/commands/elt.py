from django.core.management.base import BaseCommand

from lib.extract.arcgis.extract_from_api import extract_from_arcgis_api
from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum
from lib.extract.shapefile.extract_from_shapefile import extract_from_shapefile


class Command(BaseCommand):
    help = "Load data from external data sources, and run it through stages of data pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            "geo",
            action="store",
            choices=GeoEnum,
            type=GeoEnum,
            help="Region (sta, sd, sf) to load data for",
        )
        parser.add_argument(
            "gis_data_type",
            choices=GisDataTypeEnum,
            type=GisDataTypeEnum,
            help="Data type to load (parcel, zoning, etc.)",
        )

    def handle(self, geo: GeoEnum, gis_data_type: GisDataTypeEnum, *args, **options):
        if geo == GeoEnum.santa_ana and gis_data_type == GisDataTypeEnum.parcel:
            object_id_file = extract_from_arcgis_api(geo, gis_data_type, 0)
            extract_from_arcgis_api(geo, gis_data_type, 1, thru_data={"object_id_file": object_id_file})
        elif geo == GeoEnum.santa_ana and gis_data_type == GisDataTypeEnum.zoning:
            extract_from_shapefile(geo, gis_data_type)
        elif geo == GeoEnum.california and gis_data_type == GisDataTypeEnum.oppzone:
            extract_from_shapefile(geo, gis_data_type)
        elif geo == GeoEnum.scag and gis_data_type == GisDataTypeEnum.tpa:
            extract_from_shapefile(geo, gis_data_type)
        elif geo == GeoEnum.orange_county and gis_data_type == GisDataTypeEnum.road:
            extract_from_shapefile(geo, gis_data_type)

        else:
            raise NotImplementedError("This combination of geo and gis_data_type is not implemented yet.")
        print("DONE")
