
from django.core.management.base import BaseCommand

from elt.lib.arcgis.extract_from_api import extract_from_arcgis_api
from elt.lib.shapefile.extract_from_shapefile import extract_from_shapefile
from elt.lib.types import GisData, Juri


class Command(BaseCommand):
    help = "Load data from external data sources, and run it through stages of data pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            "geo",
            action="store",
            choices=Juri,
            type=Juri,
            help="Region (sta, sd, sf) to load data for",
        )
        parser.add_argument(
            "gis_data_type",
            choices=GisData,
            type=GisData,
            help="Data type to load (parcel, zoning, etc.)",
        )

    # def generate_meta_model(self, geo: Juri):
    #     model_cls = elt_models.__dict__[f"raw_{geo.name}_meta"]
    #     model_prefix = f"Raw{geo.value.capitalize()}"
    #     elt_mods = elt_models.__dict__.keys()
    #     related_models = [x for x in elt_mods if re.match(model_prefix, x) and not x in [f"{model_prefix}ParcelMeta"]]

    def handle(self, geo: Juri, gis_data_type: GisData, *args, **options):
        match geo, gis_data_type:
            # SF
            case Juri.sf, GisData.parcel:
                extract_from_shapefile(geo, gis_data_type)
            case Juri.sf, GisData.zoning:
                extract_from_shapefile(geo, gis_data_type)
            # case Juri.sf, GisData.meta:
            #     self.generate_meta_model(geo)

            # Orange county / santa ana
            case Juri.santa_ana, GisData.parcel:
                object_id_file = extract_from_arcgis_api(geo, gis_data_type, 0)
                extract_from_arcgis_api(geo, gis_data_type, 1, thru_data={"object_id_file": object_id_file})
            case Juri.santa_ana, GisData.zoning:
                extract_from_shapefile(geo, gis_data_type)
            case Juri.california, GisData.oppzone:
                extract_from_shapefile(geo, gis_data_type)
            case Juri.scag, GisData.tpa:
                extract_from_shapefile(geo, gis_data_type)
            case Juri.orange_county, GisData.road:
                extract_from_shapefile(geo, gis_data_type)
            case _:
                raise NotImplementedError("This combination of geo and gis_data_type is not implemented yet.")
        print("DONE: NOTE -- if you've generated new GisData, you should rerun <geo> meta to update meta models.")
        print("DONE")
