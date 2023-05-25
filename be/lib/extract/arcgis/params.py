from lib.extract.arcgis import extract_from_api
from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum
from mygeo import settings

DATA_DIR = settings.BASE_DIR / "deploy" / "data-files" / "elt"

ARCGIS_DATA_SOURCES = {
    GeoEnum.santa_ana: {  # santa ana
        "geo_name": "Santa Ana",
        GisDataTypeEnum.parcel: [  # pipeline of stages
            {
                "name": "object_ids",  # First stage -- get Object IDs from arcgis for parcels in Santa Ana
                "url": "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query",
                "custom_params": {
                    "where": "SiteAddress LIKE '%santa ana'",
                    "returnIdsOnly": "true",
                    "outFields": "AssessmentNo",
                    "f": "pjson",
                },
                "has_file_output": True,
                "is_incremental": False,
                "fetcher_fn": extract_from_api.object_id_fetcher,
            },
            {
                "name": "parcel_data",
                "url": "https://www.ocgis.com/survey/rest/services/WebApps/ParcelFeatures/FeatureServer/0/query",
                "custom_params": {
                    "where": "1=1",
                    "outFields": "*",
                    "f": "geojson",
                    "returnGeometry": "true",
                    "objectIds": "",  # this gets overwritten by the fetcher to get groups of objects
                },
                "has_file_output": False,
                "is_incremental": True,  # can be loaded incrementally
                "fetcher_fn": extract_from_api.parcel_data_fetcher,
            },
        ],
    }
}


DEFAULT_ARCGIS_PARAMS = {
    # Fields we are likely to override:
    "outFields": "AssessmentNo",  # eg "*" for all fields
    "returnGeometry": "false",  # eg True for getting parcel geom
    "where": "",  # eg "SiteAddress LIKE '%santa ana'",
    "objectIds": "",  # eg "567438,234235,234234"
    "f": "geojson",  # eg 'jsonp' or 'pbf' or 'geojson'
    "returnIdsOnly": "false",
    "returnCountOnly": "false",
    # Fields we are unlikely to override:
    "time": "",
    "geometry": "",
    "geometryType": "esriGeometryEnvelope",
    "inSR": "",
    "spatialRel": "esriSpatialRelIntersects",
    "distance": "",
    "units": "esriSRUnit_Foot",
    "relationParam": "",
    "maxAllowableOffset": "",
    "geometryPrecision": "",
    "outSR": "",
    "havingClause": "",
    "gdbVersion": "",
    "historicMoment": "",
    "returnDistinctValues": "false",
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
}
