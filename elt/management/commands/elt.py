from django.core.management.base import BaseCommand
from requests import Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from lib.extract.arcgis.extract_from_api import extract_from_arcgis_api
from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum


def ____get_santa_ana_parcels(object_ids):
    batch_size = 100
    params = {
        "where": "",
        "objectIds": ",".join([str(x) for x in object_ids["objectIds"]]),
        "time": "",
        "geometry": "",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": "",
        "units": "esriSRUnit_Foot",
        "relationParam": "",
        "outFields": "*",
        "returnGeometry": "true",
        "maxAllowableOffset": "",
        "geometryPrecision": "",
        "outSR": "",
        "havingClause": "",
        "gdbVersion": "",
        "historicMoment": "",
        "returnDistinctValues": "false",
        "returnIdsOnly": "false",
        "returnCountOnly": "false",
        "returnExtentOnly": "false",
        "orderByFields": "",
        "groupByFieldsForStatistics": "",
        "outStatistics": "",
        "returnZ": "false",
        "returnM": "false",
        "multipatchOption": "xyFootprint",
        "resultOffset": "",
        "resultRecordCount": "",
        "returnTrueCurves": "false",
        "returnExceededLimitFeatures": "false",
        "quantizationParameters": "",
        "returnCentroid": "false",
        "timeReferenceUnknownClient": "false",
        "sqlFormat": "none",
        "resultType": "",
        "featureEncoding": "esriDefault",
        "datumTransformation": "",
        "f": "geojson",
    }
    p = Request(
        "GET",
        "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query",
        params=params,
    ).prepare()
    print(p.url)
    test_url = (
        "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query?where=&"
        "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query?where=&"
        "objectIds=218485310%2C218485612%2C218504272&time=&geometry=&geometryType=esriGeometryEnvelope&"
        "objectIds=218890240%2C218890242%2C218890243&time=&geometry=&geometryType=esriGeometryEnvelope&"
        "inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%2A"
        "inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%2A"
        "&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&"
        "&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&"
        "historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&"
        "historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&"
        "returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&"
        "returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&"
        "returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&"
        "returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&"
        "returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&"
        "returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&"
        "timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&"
        "timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&"
        "datumTransformation=&f=geojson"
        "datumTransformation=&f=geojson"
    )
    my_url = (
        "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query?where=&"
        "objectIds=218890240%2C218890242%2C218890243&time=&geometry=&geometryType=esriGeometryEnvelope&"
        "inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%2A"
        "&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&"
        "historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&"
        "returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&"
        "returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&"
        "returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&"
        "timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&"
        "datumTransformation=&f=geojson"
    )
    # print(test_url)
    # assert p.url == test_url


class Command(BaseCommand):
    help = "Load data from external data sources, and run it through stages of data pipeline."

    def add_arguments(self, parser):
        # parser.add_argument('sample', nargs='+')
        pass

    def handle(self, *args, **options):
        # object_ids = get_santa_ana_object_ids()
        # object_ids = {"objectIds": [218485310, 218485612, 218504272]}

        object_id_file = extract_from_arcgis_api(
            GeoEnum.santa_ana, GisDataTypeEnum.parcel, 0, always_use_existing=False
        )
        parcels = extract_from_arcgis_api(
            GeoEnum.santa_ana, GisDataTypeEnum.parcel, 1, thru_data={"object_id_file": object_id_file}
        )

        # get_santa_ana_parcels(object_ids)
        print("DONE")
