"""
This file contains implementation for functions relating to analyzing a parcel, such as the
generation of new buildings/repurpose of old one, computing scores for scenarios, and running
scenarios in general.
"""

import random
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

MIN_BUILDING_AREA = 11  # ~150sqft
MAX_BUILDING_AREA = 111  # ~1200sqft
SETBACK_WIDTHS = [3, 0.1, 0.1]
BUFFER_SIZES = {
    "MAIN": 2,
    "ACCESSORY": 1.1,
    "ENCROACHMENT": 0.2,
}
MAX_NEW_BUILDINGS = 2
MAX_ASPECT_RATIO = 2.5
MAX_FAR = 0.6

DEFAULT_SAVE_DIR = './world/data/scenario-images/'

colorkeys = list(mcolors.XKCD_COLORS.keys())


def get_cap_ratio_score():
    return 0


def get_open_space_score(avail_geom, parcel, placed_buildings):
    """
    From Notion: Open space score: size and squareness of open space remaining after placing buildings that's
    at <10% grade. Use formula like this: Score = squarish_size / lot_size * 100, 
    where squarish_size = area of rectangle with max 2:1 aspect ratio that fits
    into the open space. Value should typically be in range of 20-40.
    """
    remaining_geom = avail_geom.difference(unary_union(placed_buildings))
    open_space_poly = find_largest_rectangles_on_avail_geom(
        remaining_geom, parcel.boundary[0], num_rects=1, max_aspect_ratio=2)[0]
    area = open_space_poly.area

    # NOTE: For now, let's scale the factor by 3 to make the score relevant (arbitrary number).
    # We might want to continue tweaking this to get something that works better
    SCALING_FACTOR = 3

    return open_space_poly, area / parcel.area[0] * 100 * SCALING_FACTOR


def get_project_size_score(total_added_area):
    # For now, we use the total size of the added buildings, scaled down by 4
    # (Each ADU has max size of approx. 111sqm), so a project with one ADU will give us around 27
    # Later, this should take construction costs into account
    return total_added_area / 4


def _get_existing_floor_area_stats(parcel, buildings):
    # Helper function to get existing stats
    # There's some overlap with parcel_lib, but keeping it here
    # as this is for analysis only
    parcel_size = parcel.geometry[0].area
    existing_living_area = parcel.total_lvg_field[0] / 10.764

    garage_area = (int(parcel.garage_sta[0] or 0) +
                   int(parcel.carport_st[0] or 0)) * 23.2

    # existing_living_area + carport/garage area
    existing_floor_area = existing_living_area + garage_area

    existing_FAR = existing_floor_area / parcel_size

    main_building_area = buildings[buildings.building_type ==
                                   'MAIN'].geometry.area.sum()
    accessory_buildings_area = buildings[buildings.building_type ==
                                         'ACCESSORY'].geometry.area.sum()

    return (parcel_size, existing_living_area, existing_floor_area,
            existing_FAR, main_building_area, accessory_buildings_area)


def better_plot(apn, address, parcel, topos, polys, open_space_poly, street_edges):
    # Plots a parcel, buildings, and new buildings
    p = parcel.plot()
    plt.title(apn + ':' + address)

    topos.plot(ax=p, color='gray')
    geopandas.GeoSeries(open_space_poly).plot(ax=p, alpha=0.4,
                                              color="lightgrey", edgecolor="green", hatch="..")

    geopandas.GeoSeries(street_edges.buffer(0.4)).plot(ax=p, color='brown')

    for idx, poly in enumerate(polys):
        geopandas.GeoSeries(poly).plot(
            ax=p, color=colorkeys[idx % len(colorkeys)], alpha=0.6)


def _analyze_one_parcel(parcel, show_plot=False, save_file=False, save_dir=DEFAULT_SAVE_DIR, try_garage_conversion=True):
    """Runs analysis on a single parcel of land

    Args:
        parcel (Parcel): A Parcel Model object that we want to analyse.
        show_plot (Boolean, optional): Shows the parcel in a GUI. Defaults to False.
        save_file (Boolean, optional): Saves the parcel to an image file. Defaults to False.
    """
    apn = parcel.apn

    buildings = get_buildings(parcel)

    if (len(buildings)) == 0:
        raise Exception(f"No buildings found for parcel: {apn}")

    topos = get_topo_lines(parcel)
    topos_df = models_to_utm_gdf(topos)

    parcel = models_to_utm_gdf([parcel])
    buildings = models_to_utm_gdf(buildings)

    identify_building_types(parcel, buildings)

    max_total_area = get_avail_floor_area(parcel, buildings, MAX_FAR)

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
        avail_geom, parcel.boundary[0], num_rects=MAX_NEW_BUILDINGS, max_aspect_ratio=MAX_ASPECT_RATIO,
        min_area=MIN_BUILDING_AREA, max_total_area=max_total_area, max_area_per_building=MAX_BUILDING_AREA)
    # Add more fields as necessary
    new_building_info = list(map(lambda poly: {
        'geometry': poly,
        'area': poly.area,
    }, new_building_polys))
    p = dict(parcel.T.to_dict())[0]
    address = f'{p["situs_pre_field"] or ""} {p["situs_addr"]} {p["situs_stre"]} {p["situs_suff"] or ""} {p["situs_post"] or ""}'

    # Get floor area info
    (parcel_size, existing_living_area, existing_floor_area,
     existing_FAR, main_building_area, accessory_buildings_area) = _get_existing_floor_area_stats(
        parcel, buildings)

    # Compute garage conversion fields
    num_garages = int(parcel.garage_sta[0] or 0)
    garage_con_units = int(
        num_garages > 0) if try_garage_conversion else 0
    # Sqm. Assume each garage/carport is 23.2sqm, or approx. 250sqft
    garage_con_area = num_garages * 23.2

    total_added_building_area = sum([poly.area for poly in new_building_polys])
    new_FAR = (total_added_building_area + existing_floor_area) / parcel_size
    # Score stuff
    cap_ratio_score = get_cap_ratio_score()
    open_space_poly, open_space_score = get_open_space_score(
        avail_geom, parcel, new_building_polys)
    project_size_score = get_project_size_score(total_added_building_area)
    total_score = cap_ratio_score + open_space_score + project_size_score

    # Get development potential limiting factor. Multiply by a factor
    # to scale it down to account for innacuracies
    limiting_factor = ""
    theoretical_avail_space = MAX_BUILDING_AREA * MAX_NEW_BUILDINGS * 0.98
    tolerance_FAR = 0.01

    if total_added_building_area < theoretical_avail_space:
        # Development potential not reached
        if new_FAR > MAX_FAR - tolerance_FAR:
            limiting_factor = 'FAR'
        else:
            limiting_factor = "Available Space"
        # Todo: Insert something about topography.

    # Do plotting stuff if necessary
    if show_plot or save_file:
        lot_df = geopandas.GeoDataFrame(
            geometry=[*buildings.geometry, parcel.geometry[0].boundary], crs="EPSG:4326")
        better_plot(apn, address, lot_df, topos_df,
                    new_building_polys, open_space_poly, parcel_edges[0])

        if show_plot:
            plt.show()
        if save_file:
            # Create the directory if it doesn't exist
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir)

            plt.savefig(save_dir + apn + ".jpg")
            plt.close()

    # Get git info
    repo = git.Repo(search_parent_directories=True)
    git_sha = repo.head.object.hexsha

    # Create the data struct that represents the test that was run
    # The order in this dictionary is the order that the fields will be written to the csv
    analyzed = {
        "apn": apn,
        "address": address,
        "num_existing_buildings": len(buildings[buildings.building_type != "ENCROACHMENT"]),

        "carports": int(parcel.carport_st[0] or 0),
        "garages": num_garages,

        "parcel_size": parcel_size,
        "existing_living_area": existing_living_area,
        "existing_floor_area": existing_floor_area,
        "existing_FAR": existing_FAR,

        "num_new_buildings": len(new_building_polys),
        "new_building_areas": ",".join([str(int(round(poly.area))) for poly in new_building_polys]),
        "total_added_building_area": total_added_building_area,
        "garage_con_units": garage_con_units,
        "garage_con_area": garage_con_area,
        "total_new_units": garage_con_units + len(new_building_polys),
        "total_added_area": garage_con_area + total_added_building_area,
        "new_FAR": new_FAR,
        "limiting_factor": limiting_factor,

        "main_building_poly_area": main_building_area,
        "accessory_buildings_polys_area": accessory_buildings_area,
        "avail_geom_area": avail_geom.area,
        "avail_area_by_FAR": max_total_area,

        "parcel_sloped_area": unary_union(too_steep).area,
        "parcel_sloped_ratio": unary_union(too_steep).area / parcel.geometry[0].area,

        "total_score": total_score,
        "cap_ratio_score": cap_ratio_score,
        "open_space_score": open_space_score,
        "project_size_score": project_size_score,

        "git_commit_hash": git_sha,
        "datetime_ran": datetime.datetime.now(),

        # To be ignored by CSV dump, but we still want to save these in the future
        "buildings": buildings.to_json(),
        "new_buildings": new_building_info,
        "input_parameters": {
            "setback_widths": SETBACK_WIDTHS,
            "building_buffer_sizes": BUFFER_SIZES,
            "max_new_buildings": MAX_NEW_BUILDINGS,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "FAR_ratio": MAX_FAR,
        },
        "no_build_zones": {
            "setbacks": setbacks,
            "buffered_buildings": buffered_buildings_geom,
            "topography": "insert",
        },
        "avail_geom": avail_geom,
    }

    return analyzed


def analyze_by_apn(apn, show_plot=False, save_file=False):
    parcel = get_parcel_by_apn(apn)
    return _analyze_one_parcel(parcel, show_plot, save_file)


def analyze_neighborhood(hood_bounds_tuple, save_file=False, save_dir=DEFAULT_SAVE_DIR, limit=None, shuffle=False):
    # Temporary, if none is provided
    if not save_dir:
        save_dir = DEFAULT_SAVE_DIR

    bounding_box = django.contrib.gis.geos.Polygon.from_bbox(
        hood_bounds_tuple)
    parcels = get_parcels_by_neighborhood(bounding_box)

    if (shuffle):
        parcels = list(parcels)
        random.shuffle(parcels)

    print(f"Found {len(parcels)} parcels. Analyzing {limit or len(parcels)}.")

    analyzed = []
    errors = []
    for i, parcel in enumerate(parcels):
        if limit and i >= int(limit):
            print("Stopping at user-requested limit of parcels.")
            break
        print(i, parcel.apn)
        try:
            result = _analyze_one_parcel(
                parcel, False, save_file, save_dir=save_dir)

            # Shouldn't need this as result should never be null,
            # but we keep it as a sanity check
            if result is not None:
                analyzed.append(result)
        except Exception as e:
            print(f"Exception on parcel {parcel.apn}")
            print(e)
            errors.append({
                "apn": parcel.apn,
                "error": e,
            })

    if save_file:
        # Export to csv
        # First, create a Pandas dataframe
        df = DataFrame.from_records(analyzed, exclude=[
            'buildings', 'input_parameters', 'no_build_zones',
            'new_buildings', 'avail_geom'])
        print(df)
        df.to_csv(
            "./world/data/scenario-images/results.csv", index=False)
        error_df = DataFrame.from_records(errors)
        error_df.to_csv("./world/data/scenario-images/errors.csv", index=False)

    print(f"Done analyzing {i+1} parcels. {len(errors)} errors")
