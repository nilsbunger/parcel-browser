from django.core.management.base import BaseCommand

from elt.lib.analysis.yigby import analyze_yigby
from elt.lib.arcgis.extract_from_api import extract_from_arcgis_api
from elt.lib.excel.extract_from_excel import extract_from_excel
from elt.lib.postprocess import postprocess_sf
from elt.lib.shapefile.extract_from_shapefile import extract_from_shapefile
from elt.lib.types import EltAnalysisEnum, GisData, Juri


class Command(BaseCommand):
    help = "Run an analysis on a set of parcels, storing result in DB for viewing."

    def add_arguments(self, parser):
        parser.add_argument(
            "geo",
            action="store",
            choices=Juri,
            type=Juri,
            help="Region (sta, sd, sf) to load data for",
        )
        parser.add_argument(
            "analysis",
            type=EltAnalysisEnum,
            help="Analysis to run (eg yigby)",
        )
        parser.add_argument(
            "--force",
            help="Overwrite previous analysis of same type",
        )

    def handle(self, geo: Juri, analysis: EltAnalysisEnum, *args, **options):
        match geo, analysis:
            # SF
            case Juri.sf, EltAnalysisEnum.yigby:
                analyze_yigby(geo)
            case _:
                raise NotImplementedError("This combination of geo and analysis is not implemented yet.")
        print("DONE")
