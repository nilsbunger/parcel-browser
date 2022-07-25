"""
This file contains implementation for functions relating to analyzing a parcel, such as the
generation of new buildings/repurpose of old one, computing scores for scenarios, and running
scenarios in general.
"""

from lib.topo_lib import get_topo_lines
from typing import Tuple
from joblib import Parallel, delayed
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
from datetime import date
from lib.types import ParcelDC
from lib.plot_lib import plot_new_buildings, plot_split_lot
from lib.zoning_rules import ZONING_FRONT_SETBACKS_IN_FEET, get_far

# TODO: It seems any workers we spawn will need django.setup(), so let's move
# all the workers to a separate file so we don't pollute this file.
django.setup()

MIN_BUILDING_AREA = 11  # ~150sqft
MAX_BUILDING_AREA = 111  # ~1200sqft
BUFFER_SIZES = {
    "MAIN": 2,
    "ACCESSORY": 1.1,
    "ENCROACHMENT": 0.2,
}
MAX_NEW_BUILDINGS = 2
MAX_ASPECT_RATIO = 2.5

DEFAULT_SAVE_DIR = './world/data/scenario-images/'

colorkeys = list(mcolors.XKCD_COLORS.keys())


def get_cap_ratio_score():
    return 0


def get_open_space_score(not_open_space: Polygonal, parcel_geom: MultiPolygon) -> tuple[Polygon, float]:
    """
    From Notion: Open space score: size and squareness of open space remaining after placing buildings that's
    at <10% grade. Use formula like this: Score = squarish_size / lot_size * 100,
    where squarish_size = area of rectangle with max 2:1 aspect ratio that fits
    into the open space. Value should typically be in range of 20-40.
    """
    remaining = parcel_geom.difference(not_open_space)
    open_space_poly = find_largest_rectangles_on_avail_geom(
        remaining, parcel_geom.boundary, num_rects=1, max_aspect_ratio=2)[0]
    area = open_space_poly.area

    # NOTE: For now, let's scale the factor by 3 to make the score relevant (arbitrary number).
    # We might want to continue tweaking this to get something that works better
    SCALING_FACTOR = 3

    return open_space_poly, area / parcel_geom.area * 100 * SCALING_FACTOR


def get_project_size_score(total_added_area):
    # For now, we use the total size of the added buildings, scaled down by 4
    # (Each ADU has max size of approx. 111sqm), so a project with one ADU will give us around 27
    # Later, this should take construction costs into account
    return total_added_area / 4


def _get_existing_floor_area_stats(parcel: ParcelDC, buildings: GeoDataFrame):
    # Helper function to get existing stats
    # There's some overlap with parcel_lib, but keeping it here
    # as this is for analysis only
    parcel_size = parcel.geometry.area
    existing_living_area = parcel.model.total_lvg_field / 10.764
    num_garages = int(
        parcel.model.garage_sta) if parcel.model.garage_sta else 0
    num_carports = int(
        parcel.model.carport_st) if parcel.model.carport_st else 0
    garage_area = (num_garages + num_carports) * 23.2

    # existing_living_area + carport/garage area
    existing_floor_area = existing_living_area + garage_area

    existing_FAR = existing_floor_area / parcel_size

    main_building_area = buildings[buildings.building_type ==
                                   'MAIN'].geometry.area.sum()
    accessory_buildings_area = buildings[buildings.building_type ==
                                         'ACCESSORY'].geometry.area.sum()

    return (parcel_size, existing_living_area, existing_floor_area,
            existing_FAR, main_building_area, accessory_buildings_area)


def get_folder_name(neighborhood: str):
    return f"{date.today()}-{neighborhood.lower()}"


def _analyze_one_parcel(parcel_model: Parcel, utm_crs: pyproj.CRS, show_plot=False,
                        save_file=False, save_dir=DEFAULT_SAVE_DIR,
                        try_garage_conversion=True, try_split_lot=True):
    """Runs analysis on a single parcel of land

    Args:
        parcel (Parcel): A Parcel Model object that we want to analyse.
        utm_crs: (pyproj.CRS): Coordinate system to use for analysis.
        show_plot (Boolean, optional): Shows the parcel in a GUI. Defaults to False.
        save_file (Boolean, optional): Saves the parcel to an image file. Defaults to False.
        save_dir (str, optional): Directory to save the generated plots/csvs to. Defaults to DEFAULT_SAVE_DIR.
        try_garage_conversion (Boolean, optional): Whether to try converting garage to an ADU. Defaults to True.
        try_split_lot (Boolean, optional): Whether to try splitting the lot into two lots. Defaults to True.
    """
    parcel = parcel_model_to_utm_dc(parcel_model, utm_crs)
    apn = parcel.model.apn

    # Get parameters based on zoning
    zone = get_parcel_zone(parcel, utm_crs)
    # Technically don't need side or rear setbacks, but buffer by a small amount
    # to account for errors
    setback_widths = (ZONING_FRONT_SETBACKS_IN_FEET[zone] / 3.28, 0.1, 0.1)

    buildings = get_buildings(parcel_model)

    if (len(buildings)) == 0:
        raise Exception(f"No buildings found for parcel: {apn}")

    topos = get_topo_lines(parcel_model)
    topos_df = models_to_utm_gdf(topos, utm_crs)

    max_far = get_far(zone, parcel.geometry.area)
    buildings = models_to_utm_gdf(buildings, utm_crs)

    identify_building_types(parcel.geometry, buildings)

    max_total_area = get_avail_floor_area(parcel, buildings, max_far)

    # Compute the spaces that we can't build on
    # First, the buffered areas around buildings
    buffered_buildings_geom = get_buffered_building_geom(
        buildings, BUFFER_SIZES)

    # Then, the setbacks around the parcel edges
    parcel_edges = get_street_side_boundaries(parcel, utm_crs)
    setbacks = get_setback_geoms(parcel.geometry, setback_widths, parcel_edges)

    # Insert Topography no-build zones - hardcoded to max 10% grade for the moment
    too_steep = get_too_steep_polys(parcel.model, utm_crs, max_slope=10)

    cant_build = unary_union(
        [*buffered_buildings_geom, *setbacks, *too_steep])
    avail_geom = get_avail_geoms(parcel.geometry, cant_build)

    new_building_polys = find_largest_rectangles_on_avail_geom(
        avail_geom, parcel.geometry, num_rects=MAX_NEW_BUILDINGS, max_aspect_ratio=MAX_ASPECT_RATIO,
        min_area=MIN_BUILDING_AREA, max_total_area=max_total_area, max_area_per_building=MAX_BUILDING_AREA)
    # Add more fields as necessary
    new_building_info = list(map(lambda poly: {
        'geometry': poly,
        'area': poly.area,
    }, new_building_polys))
    address = f'{parcel.model.situs_pre_field or ""} {parcel.model.situs_addr} {parcel.model.situs_stre} {parcel.model.situs_suff or ""} {parcel.model.situs_post or ""}'

    # Get the open space available (for yard and stuff)'
    # Question: Should setbacks be considered in open space?
    not_open_space = unary_union(
        [*buildings.geometry, *new_building_polys, *too_steep])

    # Get floor area info
    (parcel_size, existing_living_area, existing_floor_area,
     existing_FAR, main_building_area, accessory_buildings_area) = _get_existing_floor_area_stats(
        parcel, buildings)

    # Compute garage conversion fields
    num_garages = int(
        parcel.model.garage_sta) if parcel.model.garage_sta else 0
    num_carports = int(
        parcel.model.carport_st) if parcel.model.carport_st else 0
    garage_con_units = int(
        num_garages > 0) if try_garage_conversion else 0
    # Sqm. Assume each garage/carport is 23.2sqm, or approx. 250sqft
    garage_con_area = num_garages * 23.2

    total_added_building_area = sum([poly.area for poly in new_building_polys])
    new_FAR = (total_added_building_area + existing_floor_area) / parcel_size
    # Score stuff
    cap_ratio_score = get_cap_ratio_score()
    open_space_poly, open_space_score = get_open_space_score(
        not_open_space, parcel.geometry)
    project_size_score = get_project_size_score(total_added_building_area)
    total_score = cap_ratio_score + open_space_score + project_size_score

    # Get development potential limiting factor. Multiply by a factor
    # to scale it down to account for innacuracies
    limiting_factor = ""
    theoretical_avail_space = MAX_BUILDING_AREA * MAX_NEW_BUILDINGS * 0.98
    tolerance_FAR = 0.01

    if total_added_building_area < theoretical_avail_space:
        # Development potential not reached
        if new_FAR > max_far - tolerance_FAR:
            limiting_factor = 'FAR'
        else:
            limiting_factor = "Available Space"
        # Todo: Insert something about topography.

    # Logic for lot splits
    if try_split_lot:
        second_lot, second_lot_area_ratio = split_lot(
            parcel.geometry, buildings)
    else:
        second_lot, second_lot_area_ratio = None, None

    # Do plotting stuff if necessary
    if show_plot or save_file:

        # Generate the figures
        new_buildings_fig = plot_new_buildings(parcel, buildings, utm_crs, address, topos_df,
                                               new_building_polys, open_space_poly, parcel_edges[0])

        if second_lot:
            split_lot_fig = plot_split_lot(
                parcel, address, buildings, utm_crs, second_lot)

        # Save figures
        if save_file:
            new_buildings_fig.savefig(os.path.join(
                save_dir, "new-buildings", apn + ".jpg"))

            if second_lot:
                split_lot_fig.savefig(os.path.join(
                    save_dir, "lot-splits", apn + ".jpg"))

        # Show figures
        if show_plot:
            plt.show()
        plt.close()

    # Get git info
    repo = git.Repo(search_parent_directories=True)
    git_sha = repo.head.object.hexsha

    # Create the data struct that represents the test that was run
    # The order in this dictionary is the order that the fields will be written to the csv
    analyzed = {
        "apn": apn,
        "address": address,
        "zone": zone,
        "num_existing_buildings": len(buildings[buildings.building_type != "ENCROACHMENT"]),
        "carports": num_carports,
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
        "parcel_sloped_ratio": unary_union(too_steep).area / parcel.geometry.area,

        "total_score": total_score,
        "cap_ratio_score": cap_ratio_score,
        "open_space_score": open_space_score,
        "project_size_score": project_size_score,

        "can_lot_split": second_lot is not None,
        "new_lot_area_ratio": second_lot_area_ratio,
        "new_lot_area": second_lot.area if second_lot else None,

        "git_commit_hash": git_sha,
        "datetime_ran": datetime.datetime.now(),

        "front_setback": setback_widths[0],
        "max_far": max_far,

        # To be ignored by CSV dump, but we still want to save these in the future
        # "buildings": buildings.to_json(),
        "buildings": "to be implemented",
        "new_buildings": new_building_info,
        "input_parameters": {
            "setback_widths": setback_widths,
            "building_buffer_sizes": BUFFER_SIZES,
            "max_new_buildings": MAX_NEW_BUILDINGS,
            "max_aspect_ratio": MAX_ASPECT_RATIO,
            "FAR_ratio": max_far,
        },
        "no_build_zones": {
            "setbacks": setbacks,
            "buffered_buildings": buffered_buildings_geom,
            "topography": "insert",
        },
        "avail_geom": avail_geom,
    }

    return analyzed


def analyze_by_apn(apn: str, utm_crs: pyproj.CRS, show_plot=False, save_file=False):
    parcel = get_parcel_by_apn(apn)
    return _analyze_one_parcel(parcel, utm_crs, show_plot, save_file)


def _analyze_one_parcel_worker(parcel: Parcel, utm_crs: pyproj.CRS, show_plot=False,
                               save_file=False, save_dir=DEFAULT_SAVE_DIR,
                               try_garage_conversion=True, try_split_lot=True, i: int = 0):
    print(i, parcel.apn)
    try:
        result = _analyze_one_parcel(
            parcel, utm_crs, show_plot=False, save_file=save_file,
            save_dir=save_dir, try_garage_conversion=try_garage_conversion,
            try_split_lot=try_split_lot)

        # Shouldn't need this as result should never be null,
        # but we keep it as a sanity check
        assert (result is not None)
        return result, None
    except Exception as e:
        print(f"Exception on parcel {parcel.apn}")
        print(e)
        return None, {
            "apn": parcel.apn,
            "error": e,
        }


def analyze_neighborhood(hood_bounds_tuple: Tuple, zip_codes: list[str], utm_crs: pyproj.CRS,
                         hood_name: str = "", save_file=False, save_dir=None,
                         limit=None, shuffle=False, try_split_lot=True):
    # Temporary, if none is provided
    folder_name = get_folder_name(hood_name)
    if not save_dir:
        save_dir = os.path.join(DEFAULT_SAVE_DIR, folder_name, "")
    else:
        # Add a trailing slash if there isn't
        save_dir = os.path.join(save_dir, "")

    # Make folder if doesn't exist
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    if not os.path.isdir(os.path.join(save_dir, "new-buildings")):
        os.makedirs(os.path.join(save_dir, "new-buildings"))
    if not os.path.isdir(os.path.join(save_dir, "lot-splits")):
        os.makedirs(os.path.join(save_dir, "lot-splits"))

    if zip_codes:
        parcels = get_parcels_by_zip_codes(zip_codes)
    else:
        bounding_box = django.contrib.gis.geos.Polygon.from_bbox(
            hood_bounds_tuple)
        parcels = get_parcels_by_neighborhood(bounding_box)

    if (shuffle):
        parcels = list(parcels)
        random.shuffle(parcels)

    num_analyze = min(len(parcels), int(limit)) if limit else len(parcels)

    print(f"Found {len(parcels)} parcels. Analyzing {num_analyze}.")

    # Feature flag: this uses multiprocessing. Turn it off to go back to the original sequential method
    if True:
        parallel_results = Parallel(n_jobs=8)(
            delayed(_analyze_one_parcel_worker)(parcel, utm_crs, show_plot=False, save_file=save_file,
                                                save_dir=save_dir, try_split_lot=try_split_lot, i=i)
            for i, parcel in zip(range(num_analyze), parcels))

        analyzed = [x[0] for x in parallel_results if x[0] is not None]
        errors = [x[1] for x in parallel_results if x[1] is not None]
    else:
        analyzed = []
        errors = []
        i = 0
        for i, parcel in enumerate(parcels):
            if limit and i >= int(limit):
                print("Stopping at user-requested limit of parcels.")
                break
            print(i, parcel.apn)
            try:
                result = _analyze_one_parcel(
                    parcel, utm_crs, show_plot=False, save_file=save_file,
                    save_dir=save_dir, try_split_lot=try_split_lot)

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
            os.path.join(save_dir, f"{folder_name}-results.csv"), index=False)
        error_df = DataFrame.from_records(errors)
        error_df.to_csv(os.path.join(
            save_dir, f"{folder_name}-errors.csv"), index=False)

    print(f"Done analyzing {num_analyze} parcels. {len(errors)} errors")
