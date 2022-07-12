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
import os

from lib.topo_lib import get_topo_lines

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

DEFAULT_SAVE_DIR = './world/data/scenario-images/'

colorkeys = list(mcolors.XKCD_COLORS.keys())


def get_cap_ratio_score():
    return 0


def get_open_space_score(avail_geom, parcel):
    """
    From Notion: Open space score: size and squareness of open space remaining that's
    at <10% grade. Use formula like this: Score = squarish_size / lot_size * 100, 
    where squarish_size = area of rectangle with max 2:1 aspect ratio that fits
    into the open space. Value should typically be in range of 20-40.
    """
    new_building_polys = find_largest_rectangles_on_avail_geom(
        avail_geom, parcel.boundary[0], num_rects=1, max_aspect_ratio=2)
    area = new_building_polys[0].area

    return area / parcel.area[0] * 100


def get_project_size_score(total_added_area):
    # For now, we use the total size of the added buildings, scaled down by 4
    # (Each ADU has max size of approx. 111sqm), so a project with one ADU will give us around 27
    # Later, this should take construction costs into account
    return total_added_area / 4


def better_plot(apn, address, parcel, topos, polys):
    # Plots a parcel, buildings, and new buildings
    p = parcel.plot()
    plt.title(apn + ':' + address)

    topos.plot(ax=p, color='gray')

    for idx, poly in enumerate(polys):
        geopandas.GeoSeries(poly).plot(
            ax=p, color=colorkeys[idx % len(colorkeys)], alpha=0.5)


def _analyze_one_parcel(parcel, show_plot=False, save_file=False, save_dir=DEFAULT_SAVE_DIR):
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

    topos = get_topo_lines(parcel)
    topos_df = models_to_utm_gdf(topos)

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

    # Insert Topography no-build zones - hardcoded to max 10% grade for the moment
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
        p = dict(parcel.T.to_dict())[0]
        address = f'{p["situs_pre_field"] or ""} {p["situs_addr"]} {p["situs_stre"]} {p["situs_suff"] or ""} {p["situs_post"] or ""}'
        lot_df = geopandas.GeoDataFrame(
            geometry=[*buildings.geometry, parcel.geometry[0].boundary], crs="EPSG:4326")
        better_plot(apn, address, lot_df, topos_df, new_building_polys)

        if show_plot:
            plt.show()
        if save_file:
            # Create the directory if it doesn't exist
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir)

            plt.savefig(save_dir + apn + ".jpg")
            plt.close()

    total_added_area = sum([poly.area for poly in new_building_polys])

    # Score stuff
    cap_ratio_score = get_cap_ratio_score()
    open_space_score = get_open_space_score(avail_geom, parcel)
    project_size_score = get_project_size_score(total_added_area)
    total_score = cap_ratio_score + open_space_score + project_size_score

    # Get git info
    repo = git.Repo(search_parent_directories=True)
    git_sha = repo.head.object.hexsha

    # Create the data struct that represents the test that was run
    analyzed = {
        "apn": apn,
        "git_commit_hash": git_sha,
        "datetime_ran": datetime.datetime.now(),

        "buildings": buildings.to_json(),
        "num_existing_buildings": len(buildings),
        "parcel_size": parcel.geometry[0].area,

        "input_parameters": {
            "setback_widths": SETBACK_WIDTHS,
            "building_buffer_sizes": BUFFER_SIZES,
            "max_rects": MAX_RECTS,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "FAR_ratio": MAX_FAR,
        },

        "no_build_zones": {
            "setbacks": setbacks,
            "buffered_buildings": buffered_buildings_geom,
            "topography": "insert",
        },
        "new_buildings": new_building_info,
        "num_new_buildings": len(new_building_polys),
        "total_added_area": total_added_area,
        "avail_geom": avail_geom,

        "avail_geom_area": avail_geom.area,
        "avail_area_by_FAR": max_area,

        "total_score": total_score,
        "cap_ratio_score": cap_ratio_score,
        "open_space_score": open_space_score,
        "project_size_score": project_size_score,
    }

    return analyzed


def analyze_by_apn(apn, show_plot=False, save_file=False):
    parcel = get_parcel_by_apn(apn)
    return _analyze_one_parcel(parcel, show_plot, save_file)


def analyze_neighborhood(hood_bounds_tuple, save_file=False, save_dir=DEFAULT_SAVE_DIR):
    # Temporary, if none is provided
    if not save_dir:
        save_dir = DEFAULT_SAVE_DIR

    bounding_box = django.contrib.gis.geos.Polygon.from_bbox(
        hood_bounds_tuple)
    parcels = get_parcels_by_neighborhood(bounding_box)

    print(f"Found {len(parcels)} parcels to analyze")

    analyzed = []
    error_count = 0
    for i, parcel in enumerate(parcels):
        if i >= 2000:
            break
        print(i, parcel.apn)
        try:
            analyzed.append(_analyze_one_parcel(
                parcel, False, save_file, save_dir=save_dir))
        except Exception as e:
            print(f"Exception on parcel {parcel.apn}")
            print(e)
            error_count += 1

    if save_file:
        # Export to csv
        # First, create a Pandas dataframe
        df = DataFrame.from_records(analyzed, exclude=[
            'buildings', 'input_parameters', 'no_build_zones',
            'new_buildings', 'avail_geom'])
        print(df)
        df.to_csv(
            "./world/data/scenario-images/results.csv", index=False)

    print(f"Done analyzing {len(parcels)} parcels. {error_count} errors")
