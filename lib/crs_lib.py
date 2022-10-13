import pyproj
from pyproj import CRS, Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info


def get_utm_crs() -> pyproj.CRS:
    print("Using San Diego UTM CRS")
    # These two versions should be equivalent:
    # sd_utm_crs = pyproj.CRS.from_wkt(SAN_DIEGO_UTM_CRS_WKT)
    sd_utm_crs = pyproj.CRS(proj="utm", zone=11, ellps="WGS84")
    return sd_utm_crs


from math import cos, sin, asin, sqrt, radians


def latlong_to_utm_crs(lat, long):
    """Return a CRS object for the UTM zone that contains the given lat/long"""
    # From https://pyproj4.github.io/pyproj/stable/examples.html#find-utm-crs-by-latitude-and-longitude
    utm_crs_list = query_utm_crs_info(
        datum_name="WGS 84",
        area_of_interest=AreaOfInterest(
            west_lon_degree=long,
            south_lat_degree=lat,
            east_lon_degree=long,
            north_lat_degree=lat,
        ),
    )
    utm_crs = CRS.from_epsg(utm_crs_list[0].code)
    return utm_crs


def meters_to_latlong(meters, baselat, baselong):
    crs = latlong_to_utm_crs(baselat, baselong)
    (base_x, base_y) = Transformer.from_crs("epsg:4326", crs).transform(baselat, baselong)
    transformer = Transformer.from_crs(crs_from=crs, crs_to="EPSG:4326")
    (lat1, long1) = transformer.transform(meters + base_x, meters + base_y)
    (lat2, long2) = transformer.transform(base_x, base_y)
    return (lat1 - lat2, long1 - long2)


def latlong_to_meters(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees). Return value in meters.
    Haversine Formula
    Ref: https://gis.stackexchange.com/questions/61924/python-gdal-degrees-to-meters-without-reprojecting
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371000 * c
    return km


# Well-known text of San Diego region UTM projection (UTM Zone 11 North). This is the coordinate system
# we use for our shapely-based geometry calculations.
SAN_DIEGO_UTM_CRS_WKT = """
PROJCRS["WGS 84 / UTM zone 11N",
        BASEGEOGCRS["WGS 84",
                    ENSEMBLE["World Geodetic System 1984 ensemble",
                             MEMBER["World Geodetic System 1984 (Transit)"],
                             MEMBER["World Geodetic System 1984 (G730)"],
                             MEMBER["World Geodetic System 1984 (G873)"],
                             MEMBER["World Geodetic System 1984 (G1150)"],
                             MEMBER["World Geodetic System 1984 (G1674)"],
                             MEMBER["World Geodetic System 1984 (G1762)"],
                             MEMBER["World Geodetic System 1984 (G2139)"],
                             ELLIPSOID["WGS 84",6378137,298.257223563,
                                       LENGTHUNIT["metre",1]],
                             ENSEMBLEACCURACY[2.0]],
                    PRIMEM["Greenwich",0,
                           ANGLEUNIT["degree",0.0174532925199433]],
                    ID["EPSG",4326]],
        CONVERSION["UTM zone 11N",
                   METHOD["Transverse Mercator",
                          ID["EPSG",9807]],
                   PARAMETER["Latitude of natural origin",0,
                             ANGLEUNIT["degree",0.0174532925199433],
                             ID["EPSG",8801]],
                   PARAMETER["Longitude of natural origin",-117,
                             ANGLEUNIT["degree",0.0174532925199433],
                             ID["EPSG",8802]],
                   PARAMETER["Scale factor at natural origin",0.9996,
                             SCALEUNIT["unity",1],
                             ID["EPSG",8805]],
                   PARAMETER["False easting",500000,
                             LENGTHUNIT["metre",1],
                             ID["EPSG",8806]],
                   PARAMETER["False northing",0,
                             LENGTHUNIT["metre",1],
                             ID["EPSG",8807]]],
        CS[Cartesian,2],
        AXIS["(E)",east,
             ORDER[1],
             LENGTHUNIT["metre",1]],
        AXIS["(N)",north,
             ORDER[2],
             LENGTHUNIT["metre",1]],
        USAGE[
            SCOPE["Engineering survey, topographic mapping."],
            AREA["Between 120°W and 114°W, northern hemisphere between equator and 84°N, onshore and offshore. Canada - Alberta; British Columbia (BC); Northwest Territories (NWT); Nunavut. Mexico. United States (USA)."],
            BBOX[0,-120,84,-114]],
        ID["EPSG",32611]]
"""
