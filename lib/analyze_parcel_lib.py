from lib.parcel_lib import *
from shapely.ops import unary_union
import geopandas
import matplotlib.pyplot as plt
import git
import matplotlib.colors as mcolors
import datetime

MIN_AREA = 11  # ~150sqft
MAX_AREA = 111  # ~1200sqft
SETBACK_WIDTHS = [3, 0.1, 0.1]
BUFFER_SIZES = {
    "MAIN": 2,
    "ACCESSORY": 1.1,
    "ENCROACHMENT": 0.2,
}

colorkeys = list(mcolors.XKCD_COLORS.keys())


def better_plot(apn, parcel, polys):
    p = parcel.plot()
    plt.title(apn)
    for idx, poly in enumerate(polys):
        geopandas.GeoSeries(poly).plot(
            ax=p, color=colorkeys[idx % len(colorkeys)], alpha=0.5)


def analyze_one_parcel(apn, show_plot=False, save_file=False):
    parcel, buildings = get_parcel_and_buildings_gdf(apn)
    identify_building_types(parcel, buildings)

    # Compute the spaces that we can't build on
    # First, the buffered areas around buildings
    buffered_buildings_geom = get_buffered_building_geom(
        buildings, BUFFER_SIZES)

    # Then, the setbacks around the parcel edges
    parcel_edges = get_street_side_boundaries(parcel)
    setbacks = get_setback_geoms(parcel, SETBACK_WIDTHS, parcel_edges)

    # Insert Topography no-build zones

    cant_build = unary_union([*buffered_buildings_geom, *setbacks])
    avail_geom = get_avail_geoms(parcel.geometry[0], cant_build)

    new_building_polys = find_largest_rectangles_on_avail_geom(
        avail_geom, parcel.boundary[0], num_rects=4, max_aspect_ratio=2.5,
        min_area=MIN_AREA, max_area=MAX_AREA)
    # Add more fields as necessary
    new_building_info = list(map(lambda poly: {
        'geometry': poly,
        'area': poly.area,
    }, new_building_polys))

    # Display a graphic showing the parcel, building, and new buildings
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry[0].boundary], crs="EPSG:4326")
    better_plot(apn, lot_df, new_building_polys)

    plt.show()

    # Get git info
    repo = git.Repo(search_parent_directories=True)
    git_sha = repo.head.object.hexsha

    # Create the data struct that represents the test that was run
    analyzed = {
        "apn": apn,
        "git_commit_hash": git_sha,
        "datetime_ran": datetime.datetime.now(),

        "buildings": buildings.to_json(),
        "parcel_size": parcel.geometry[0].area,

        "input_parameters": {
            "setback_widths": SETBACK_WIDTHS,
            "building_buffer_sizes": BUFFER_SIZES,
            "num_rects": 2,
            "max_aspect_ratio": 2.5,
            "FAR_ratio": 0.6,
        },

        "no_build_zones": {
            "setbacks": setbacks,
            "buffered_buildings": buffered_buildings_geom,
            "topography": "insert",
        },
        "new_buildings": new_building_info,
        "avail_geom": avail_geom,
        "others": {}

        # Financial modelling stuff
        # Log stuff
    }

    return analyzed
