"""
This file contains implementation for functions relating to analyzing a parcel, such as the
generation of new buildings/repurpose of old one, computing scores for scenarios, and running
scenarios in general.
"""

from pandas import DataFrame
from lib.parcel_lib import *
from shapely.ops import unary_union
import geopandas
import matplotlib.pyplot as plt
import git
import matplotlib.colors as mcolors
import datetime
import django

MIN_AREA = 11  # ~150sqft
MAX_AREA = 111  # ~1200sqft
SETBACK_WIDTHS = [3, 0.1, 0.1]
BUFFER_SIZES = {
    "MAIN": 2,
    "ACCESSORY": 1.1,
    "ENCROACHMENT": 0.2,
}
MAX_RECTS = 2
MAX_ASPECT_RATIO = 2.5
MAX_FAR = 0.6

colorkeys = list(mcolors.XKCD_COLORS.keys())


def better_plot(apn, parcel, polys):
    # Plots a parcel, buildings, and new buildings
    p = parcel.plot()
    plt.title(apn)
    for idx, poly in enumerate(polys):
        geopandas.GeoSeries(poly).plot(
            ax=p, color=colorkeys[idx % len(colorkeys)], alpha=0.5)


def _analyze_one_parcel(parcel, show_plot=False, save_file=False):
    """Runs analysis on a single parcel of land

    Args:
        parcel (Parcel): A Parcel Model object that we want to analyse.
        show_plot (Boolean, optional): Shows the parcel in a GUI. Defaults to False.
        save_file (Boolean, optional): Saves the parcel to an image file. Defaults to False.
    """
    apn = parcel.apn

    buildings = get_buildings(parcel)

    if (len(buildings)) == 0:
        print("No buildings found for parcel: ", apn)
        return

    parcel = models_to_utm_gdf([parcel])
    buildings = models_to_utm_gdf(buildings)

    identify_building_types(parcel, buildings)

    max_area = min(get_avail_floor_area(parcel, buildings, MAX_FAR), MAX_AREA)

    # Compute the spaces that we can't build on
    # First, the buffered areas around buildings
    buffered_buildings_geom = get_buffered_building_geom(
        buildings, BUFFER_SIZES)

    # Then, the setbacks around the parcel edges
    parcel_edges = get_street_side_boundaries(parcel)
    setbacks = get_setback_geoms(parcel, SETBACK_WIDTHS, parcel_edges)

    # Insert Topography no-build zones
    too_steep = get_too_steep_polys(parcel, 10)

    cant_build = unary_union(
        [*buffered_buildings_geom, *setbacks, *too_steep])
    avail_geom = get_avail_geoms(parcel.geometry[0], cant_build)

    new_building_polys = find_largest_rectangles_on_avail_geom(
        avail_geom, parcel.boundary[0], num_rects=MAX_RECTS, max_aspect_ratio=MAX_ASPECT_RATIO,
        min_area=MIN_AREA, max_area=max_area)
    # Add more fields as necessary
    new_building_info = list(map(lambda poly: {
        'geometry': poly,
        'area': poly.area,
    }, new_building_polys))

    # Do plotting stuff if necessary
    if show_plot or save_file:
        lot_df = geopandas.GeoDataFrame(
            geometry=[*buildings.geometry, parcel.geometry[0].boundary], crs="EPSG:4326")
        better_plot(apn, lot_df, new_building_polys)

        if show_plot:
            plt.show()
        if save_file:
            plt.savefig("./world/data/scenario-images/" + apn + ".jpg")
            plt.close()

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


def analyze_by_apn(apn, show_plot=False, save_file=False):
    parcel = get_parcel_by_apn(apn)
    return _analyze_one_parcel(parcel, show_plot, save_file)


def analyze_neighborhood(hood_bounds_tuple, show_plot=False, save_file=False):
    bounding_box = django.contrib.gis.geos.Polygon.from_bbox(
        hood_bounds_tuple)
    parcels = get_parcels_by_neighborhood(bounding_box)

    print(f"Found {len(parcels)} parcels to analyze")

    for i, parcel in enumerate(parcels):
        print(i, parcel.apn)
        _analyze_one_parcel(parcel, False, False)

    print(f"Done analyzing {len(parcels)} parcels")
