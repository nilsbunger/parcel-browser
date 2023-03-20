"""
This file contains implementation for functions relating to analyzing a parcel, such as the
generation of new buildings/repurpose of old one, computing financial models, and running
scenarios in general.
"""
import logging
import pprint
import secrets
from collections import Counter, OrderedDict

import boto3
import django
import pyproj
from botocore.exceptions import ClientError
from geopandas import GeoDataFrame
from shapely.ops import unary_union

from lib.neighborhoods import HIGH_PRIORITY_NEIGHBORHOODS
from lib.parcel_lib import (
    find_largest_rectangles_on_avail_geom,
    get_avail_floor_area,
    get_buffered_building_geom,
    get_buildings,
    get_parcel_zone,
    get_setback_geoms,
    get_street_side_boundaries,
    get_too_high_or_low,
    identify_building_types,
    identify_flag,
    models_to_utm_gdf,
    parcel_model_to_utm_dc,
    split_lot,
)
from lib.types import ParcelDC
from world.models.base_models import Parcel
from world.models.models import AnalyzedListing, PropertyListing

# TODO: It seems any workers we spawn will need django.setup(), so let's move
# all the workers to a separate file so we don't pollute this file.
if __name__ == "__main__":
    django.setup()

import datetime
import os
from datetime import date

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from joblib import Parallel, delayed

from lib.build_lib import DevScenario
from lib.finance_lib import Financials
from lib.plot_lib import plot_cant_build, plot_new_buildings, plot_split_lot
from lib.re_params import ReParams, get_build_specs
from lib.rent_lib import RentService
from lib.topo_lib import calculate_slopes_for_parcel, get_topo_lines
from lib.zoning_rules import ZONING_FRONT_SETBACKS_IN_FEET, get_far
from mygeo.settings import CLOUDFLARE_R2_ENABLED, env
from mygeo.util import eprint

log = logging.getLogger(__name__)

# Connector to Cloudflare R2 for storing images. Ironically the instructions say to use the S3 API client!
cloudflare_r2 = None
if CLOUDFLARE_R2_ENABLED:
    cloudflare_r2 = boto3.resource(
        "s3",
        endpoint_url=env("R2_ENDPOINT_URL"),
        aws_access_key_id=env("R2_EDIT_ACCESS_KEY"),
        aws_secret_access_key=env("R2_EDIT_SECRET_KEY"),
    )
else:
    print("Cloudflare R2 is disabled")
R2_BUCKET_NAME = "parsnip-images"

MIN_BUILDING_AREA = 11  # ~150sqft
MAX_BUILDING_AREA = 111  # ~1200sqft
BUFFER_SIZES = {
    "MAIN": 2,
    "ACCESSORY": 1.1,
    "ENCROACHMENT": 0.2,
}
MAX_NEW_BUILDINGS = 2
MAX_ASPECT_RATIO = 2.5

colorkeys = list(mcolors.XKCD_COLORS.keys())


def save_and_upload_figures(
    new_buildings_fig,
    cant_build_fig,
    split_lot_fig,
    salt: str,
    save_dir: str,
    apn: str,
    addr: str,
    messages: dict[str, list[str]],
    save_to_cloud: bool,
) -> None:
    # Save figures
    new_buildings_fname = os.path.join(save_dir, "buildings-" + apn + ".jpg")
    new_buildings_fig.savefig(new_buildings_fname)
    cant_build_fname = os.path.join(save_dir, "cant-build-" + apn + ".jpg")
    cant_build_fig.savefig(cant_build_fname)

    if split_lot_fig:
        split_lot_fig.savefig(os.path.join(save_dir, "lot-splits-" + apn + ".jpg"))
    if save_to_cloud:
        print(f"**** SAVING images for address {addr} to Cloudflare R2 ****")
        try:
            cloudflare_r2.meta.client.upload_file(new_buildings_fname, R2_BUCKET_NAME, f"buildings-{apn}-{salt}")
            cloudflare_r2.meta.client.upload_file(cant_build_fname, R2_BUCKET_NAME, f"cant_build-{apn}-{salt}")
        except ClientError as e:
            eprint(f"ERROR uploading images for {addr} to R2. Error = {e}")
            messages["warning"].append(f"ERROR uploading images for {addr} to R2")


def _get_existing_floor_area_stats(parcel: ParcelDC, buildings: GeoDataFrame):
    # Helper function to get existing stats
    # There's some overlap with parcel_lib, but keeping it here
    # as this is for analysis only
    parcel_size = parcel.geometry.area
    existing_living_area = parcel.model.total_lvg_field / 10.764
    num_garages = int(parcel.model.garage_sta) if parcel.model.garage_sta else 0
    num_carports = int(parcel.model.carport_st) if parcel.model.carport_st else 0
    garage_area = (num_garages + num_carports) * 23.2

    # existing_living_area + carport/garage area
    existing_floor_area = existing_living_area + garage_area

    existing_FAR = existing_floor_area / parcel_size
    if buildings is not None:
        main_building_area = buildings[buildings.building_type == "MAIN"].geometry.area.sum()
        accessory_buildings_area = buildings[buildings.building_type == "ACCESSORY"].geometry.area.sum()
    else:
        main_building_area = accessory_buildings_area = 0
    return (
        parcel_size,
        existing_living_area,
        existing_floor_area,
        existing_FAR,
        main_building_area,
        accessory_buildings_area,
    )


def get_folder_name(neighborhood: str):
    return f"{date.today()}-{neighborhood.lower()}"


rent_data = RentService()


def _dev_potential_by_far(
    property_listing: PropertyListing,
    existing_units_rents: [int],
    messages: any,
    interp_dist: int,
    is_mf: bool,
    far_area: int,
    geom_area: int,
    re_params: ReParams,
    dry_run: bool,
) -> list[DevScenario]:
    valid_scenarios = []
    existing_units_rent = sum(existing_units_rents)
    if is_mf:
        # can typically do as many ADUs as there are current units
        existing_unit_qty = property_listing.parcel.unitqty
        max_units_to_build = 3 if property_listing.parcel.unitqty == 1 else existing_unit_qty
        avail_far_sq_ft = far_area * 3.28 * 3.28
        avail_area_sq_ft = geom_area * 3.28 * 3.28
        # try scenarios:
        #   * existing_unit_qty large ADUs (1-story)
        #   * existing_unit_qty large ADUs (2-story)
        #   * existing_unit_qty small ADUs (1-story)
        #   * existing_unit_qty small ADUs (2-story)
        #   If those fail, reduce quantity and try again

        for adu_qty in range(max_units_to_build, 0, -1):
            assert adu_qty >= 1
            if valid_scenarios:
                # no need to calculate fewer # of units if we have a working strategy with more units.
                break
            for adu_unit_spec in get_build_specs(re_params.constr_costs):
                adu_sq_ft = adu_unit_spec.sqft * adu_qty
                adu_lot_space = adu_unit_spec.lotspace_required * adu_qty

                if adu_sq_ft <= avail_far_sq_ft and adu_lot_space <= avail_area_sq_ft:
                    # have a valid scenario. let's cost it out
                    # rent we can get:
                    new_units_rents = adu_qty * rent_data.rent_for_location(
                        property_listing,
                        [adu_unit_spec],
                        messages,
                        dry_run,
                        percentile=re_params.new_unit_rent_percentile,
                        is_adu=True,
                        interpolate_distance=interp_dist,
                    )
                    if len(new_units_rents) >= 1:
                        new_units_rent = sum(new_units_rents)
                    else:
                        print(f"Couldn't find rents at {property_listing.addr}")
                        new_units_rent = 0
                    # acquisition and construction costs:
                    finances = Financials()
                    constr_soft_cost = adu_sq_ft * re_params.constr_costs.soft_cost_rate
                    constr_hard_cost = adu_unit_spec.hard_build_cost * adu_qty
                    constr_adu_fees = 14000 + 10000 * adu_qty
                    if not property_listing.price:
                        # no price => can't model finances but can still record unit config
                        valid_scenarios.append(DevScenario(adu_qty=adu_qty, unit_type=adu_unit_spec, finances=None))
                        continue

                    try:
                        finances.capital_flow["acquisition"] = [
                            ("purchase", 0 - property_listing.price, ""),
                            ("renovation", -50000, ""),
                        ]
                    except Exception as e:
                        log.error(e, exc_info=True)
                        raise
                    finances.capital_flow["construction"] = [
                        (
                            "hard costs",
                            0 - constr_hard_cost,
                            f"${adu_unit_spec.hard_cost_per_sqft} / sqft for {adu_unit_spec.stories} stories",
                        ),
                        (
                            "soft costs",
                            0 - constr_soft_cost,
                            f"${re_params.constr_costs.soft_cost_rate} / sqft",
                        ),
                        (
                            "adu fees",
                            0 - constr_adu_fees,
                            "$14K base plus $10K per unit (total guess)",
                        ),
                    ]
                    total_constr_cost = constr_hard_cost + constr_soft_cost + constr_adu_fees
                    vacancy_cost = 0 - round(re_params.vacancy_rate * (new_units_rent + existing_units_rent))
                    insurance_cost = round(
                        (0 - property_listing.price + total_constr_cost) * re_params.insurance_cost_rate / 12
                    )
                    repair_cost = 0 - round(re_params.repair_cost_rate * (new_units_rent + existing_units_rent))
                    prop_taxes = round(
                        0 - (property_listing.price + total_constr_cost) * re_params.prop_tax_rate / 12
                    )
                    mgmt_cost = 0 - round(re_params.mgmt_cost_rate * (new_units_rent + existing_units_rent))
                    finances.operating_flow = [
                        [
                            "rent: existing units",
                            existing_units_rent,
                            f"{re_params.existing_unit_rent_percentile}th percentile",
                        ],
                        [
                            "rent: new units",
                            new_units_rent,
                            f"{re_params.new_unit_rent_percentile}th percentile",
                        ],
                        ["vacancy", vacancy_cost, f"{re_params.vacancy_rate * 100}% vacancy"],
                        [
                            "insurance",
                            insurance_cost,
                            f"{re_params.insurance_cost_rate * 100}% of prop value",
                        ],
                        [
                            "repairs/maint",
                            repair_cost,
                            f"{re_params.repair_cost_rate * 100}% of rent",
                        ],
                        ["prop mgmt", mgmt_cost, f"{re_params.mgmt_cost_rate * 100}% of rent"],
                        [
                            "prop taxes",
                            prop_taxes,
                            f"{re_params.prop_tax_rate * 100}% of prop value",
                        ],
                    ]

                    valid_scenarios.append(DevScenario(adu_qty=adu_qty, unit_type=adu_unit_spec, finances=finances))
                # else:
                #     print (f"Skipping putting {adu_qty} x {adu_scenario} units on lot, not enough room."
                #            f"FAR avail={avail_far_sq_ft}, geom avail={avail_area_sq_ft}"
                #            )
        log.info(
            f"For {property_listing.parcel.address} - APN {property_listing.parcel.apn} - FAR area,geom area "
            f"avail={round(avail_far_sq_ft), round(avail_area_sq_ft)} - we found these scenarios:"
        )
        log.info(f"{pprint.pformat(valid_scenarios)}")

    return valid_scenarios


def analyze_one_parcel(
    parcel_model: Parcel,
    utm_crs: pyproj.CRS,
    property_listing: PropertyListing,
    dry_run: bool,
    save_dir: str,  # this used to have a default, but it shouldn't be used
    show_plot: bool = False,
    try_garage_conversion: bool = True,
    try_split_lot: bool = True,
    force_uploads: bool = False,
) -> AnalyzedListing:
    """Runs analysis on a single parcel of land

    Args:
        parcel_model (Parcel): A Parcel Model object that we want to analyse.
        utm_crs: (pyproj.CRS): Coordinate system to use for analysis.
        property_listing (PropertyListing):
        dry_run (Boolean):
        save_dir (str): Directory to save the generated plots/csvs to. Defaults to DEFAULT_SAVE_DIR.
        show_plot (Boolean, optional): Shows the parcel in a GUI. Defaults to False.
        try_garage_conversion (Boolean, optional): Whether to try converting garage to an ADU. Defaults to True.
        try_split_lot (Boolean, optional): Whether to try splitting the lot into two lots. Defaults to True.
        force_uploads (Boolean, optional): Whether to force new uploads of images to R2.
    """

    log.info(
        f"Parcel analysis: APN={parcel_model.apn}, addr={property_listing.addr if property_listing else 'No listing'}"
    )
    re_params = ReParams()
    too_high_df = too_low_df = buffered_buildings_geom = None

    parcel = parcel_model_to_utm_dc(parcel_model, utm_crs)
    apn = parcel.model.apn
    messages = {"info": [], "warning": [], "error": [], "note": [], "stats": Counter({})}
    # *** 1. Get information about the parcel

    # Get parameters based on zoning
    zone, is_tpa, is_mf = get_parcel_zone(parcel, utm_crs)

    # Technically don't need side or rear setbacks, but buffer by a small amount
    # to account for errors
    if zone in ZONING_FRONT_SETBACKS_IN_FEET:
        front_setback = ZONING_FRONT_SETBACKS_IN_FEET[zone] / 3.28
        max_far = get_far(zone, parcel.geometry.area)
    else:
        front_setback = 5
        max_far = 0.6
        messages["warning"].append("Missing zone data for FAR and setbacks")
    setback_widths = {"front": front_setback, "side": None, "back": None, "alley": None}

    # Compute the spaces that we can't build on
    # Then, the setbacks around the parcel edges
    parcel_edges = get_street_side_boundaries(parcel, utm_crs)
    setbacks = get_setback_geoms(parcel.geometry, setback_widths, parcel_edges)

    # Insert Topography no-build zones - hardcoded to max 10% grade for the moment
    too_steep = calculate_slopes_for_parcel(parcel, utm_crs, 10, use_cache=True)
    topos = get_topo_lines(parcel_model)
    topos_df = models_to_utm_gdf(topos, utm_crs)

    buildings = get_buildings(parcel_model)
    if not len(buildings):
        log.info(f"No buildings found for parcel: {apn}")
        messages["warning"].append(f"No buildings found for parcel: {apn}")
        buildings = None
        cant_build = unary_union([*setbacks])
    else:
        buildings = models_to_utm_gdf(list(buildings), utm_crs)
        identify_building_types(parcel.geometry, buildings)
        buffered_buildings_geom = get_buffered_building_geom(buildings, BUFFER_SIZES)
        too_high_df, too_low_df, cant_build_elev = get_too_high_or_low(parcel, buildings, topos_df, utm_crs)
        cant_build = unary_union([buffered_buildings_geom, *setbacks, *too_steep, cant_build_elev])

    avail_area_by_far = get_avail_floor_area(parcel, buildings, max_far)

    flag_poly = identify_flag(parcel, parcel_edges["front"])
    if flag_poly:
        cant_build = unary_union([cant_build, flag_poly])

    # open space on the parcel
    avail_geom = parcel.geometry.difference(cant_build)

    # Get floor area info
    (
        parcel_size,
        existing_living_area,
        existing_floor_area,
        existing_far,
        main_building_area,
        accessory_buildings_area,
    ) = _get_existing_floor_area_stats(parcel, buildings)

    # *** 2a. Compute rent for existing unit.
    existing_units = property_listing.parcel.rental_units
    if property_listing.neighborhood in HIGH_PRIORITY_NEIGHBORHOODS:
        interp_dist = 500 if is_mf else 1000
    else:
        interp_dist = 3000
    existing_units_rents = rent_data.rent_for_location(
        property_listing,
        existing_units,
        messages,
        dry_run,
        percentile=re_params.existing_unit_rent_percentile,
        interpolate_distance=interp_dist,
    )
    existing_units_with_rent = list(zip([x.dict() for x in existing_units], existing_units_rents))

    if (
        not len(existing_units_rents)
        and property_listing.br
        and property_listing.br > 0
        and property_listing.ba
        and property_listing.ba > 0
    ):
        log.debug("HUH")

    # *** 2b. See what we can build on the lot, FAR-centric.
    assert property_listing
    dev_scenarios: list[DevScenario] = _dev_potential_by_far(
        property_listing,
        existing_units_rents,
        messages,
        interp_dist,
        is_mf,
        int(avail_area_by_far),
        int(avail_geom.area),
        re_params,
        dry_run,
    )
    # *** 2c. See what we can build on the lot -- geometry-focused
    new_building_polys = find_largest_rectangles_on_avail_geom(
        avail_geom,
        parcel.geometry,
        num_rects=MAX_NEW_BUILDINGS,
        max_aspect_ratio=MAX_ASPECT_RATIO,
        min_area=MIN_BUILDING_AREA,
        max_total_area=avail_area_by_far,
        max_area_per_building=MAX_BUILDING_AREA,
    )

    # Compute garage conversion fields
    num_garages = parcel_model.garages
    num_carports = parcel_model.carports
    garage_con_units = int(num_garages > 0) if try_garage_conversion else 0
    # Sqm. Assume each garage/carport is 23.2sqm, or approx. 250sqft
    garage_con_area = num_garages * 23.2

    total_added_building_area = sum([poly.area for poly in new_building_polys])
    new_far = (total_added_building_area + existing_floor_area) / parcel_size

    # Logic for lot splits
    second_lot, second_lot_area_ratio = None, None
    if try_split_lot:
        # noinspection PyBroadException
        try:
            second_lot, second_lot_area_ratio = split_lot(parcel.geometry, buildings)
        except Exception:
            messages["note"].append("Lot split attempt failed with exception")

    # 3. *** Plot and/or save results
    plt.close()
    # Generate the figures
    new_buildings_fig = plot_new_buildings(
        parcel,
        buildings,
        utm_crs,
        topos_df,
        too_high_df,
        too_low_df,
        new_building_polys,
        parcel_edges["front"],
        flag_poly,
    )
    cant_build_fig = plot_cant_build(
        parcel,
        buildings,
        utm_crs,
        buffered_buildings_geom,
        list(setbacks),
        too_steep,
        flag_poly,
        parcel_edges["front"],
    )
    split_lot_fig = plot_split_lot(parcel, buildings, utm_crs, second_lot) if second_lot else None
    # Show figures
    if show_plot:
        plt.show()
    max_cap_rate = 0
    if dev_scenarios:
        cap_rates = [scenario.finances.cap_rate_calc for scenario in dev_scenarios if scenario.finances]
        cap_rates.append(0)  # in case there are no scenarios with finances
        max_cap_rate = max(cap_rates)

    num_existing_buildings = len(buildings[buildings.building_type != "ENCROACHMENT"]) if buildings is not None else 0
    # Create the data struct that represents the test that was run
    # The order in this dictionary is the order that the fields will be written to the csv
    details = OrderedDict(
        {
            "apn": apn,
            "address": parcel.model.address,
            "existing_units_with_rent": existing_units_with_rent,
            "num_existing_buildings": num_existing_buildings,
            "carports": num_carports,
            "garages": num_garages,
            "re_params": re_params.dict(),
            "max_cap_rate": max_cap_rate,
            "parcel_size": parcel_size,
            "existing_living_area": existing_living_area,
            "existing_floor_area": existing_floor_area,
            "existing_FAR": existing_far,
            "max_FAR": max_far,
            "potential_FAR": max_far - existing_far,
            "avail_area_by_FAR": avail_area_by_far,
            "num_new_buildings": len(new_building_polys),
            "new_building_areas": ",".join([str(int(round(poly.area))) for poly in new_building_polys]),
            "total_added_building_area": total_added_building_area,
            "garage_con_units": garage_con_units,
            "garage_con_area": garage_con_area,
            "total_new_units": garage_con_units + len(new_building_polys),
            "total_added_area": garage_con_area + total_added_building_area,
            "new_FAR": new_far,
            # "limiting_factor": limiting_factor,
            "is_flag_lot": flag_poly is not None,
            "is_alley_lot": parcel_edges["alley"] is not None,
            "main_building_poly_area": main_building_area,
            "accessory_buildings_polys_area": accessory_buildings_area,
            "avail_geom_area": avail_geom.area,
            "parcel_sloped_area": unary_union(too_steep).area,
            "parcel_sloped_ratio": unary_union(too_steep).area / parcel.geometry.area,
            "can_lot_split": second_lot is not None,
            "new_lot_area_ratio": second_lot_area_ratio,
            "new_lot_area": second_lot.area if second_lot else None,
            "front_setback": setback_widths["front"],
            "messages": messages,
        }
    )

    input_parameters = {
        "setback_widths": setback_widths,
        "building_buffer_sizes": BUFFER_SIZES,
        "max_new_buildings": MAX_NEW_BUILDINGS,
        "max_aspect_ratio": MAX_ASPECT_RATIO,
        "FAR_ratio": max_far,
    }

    datetime_ran = datetime.datetime.now(datetime.timezone.utc)
    # Save it as a database model, and return it
    dev_scenarios_dict = [x.dict(exclude={"constr_costs"}) for x in dev_scenarios]
    al_defaults = {
        "datetime_ran": datetime_ran,
        "is_tpa": is_tpa,
        "is_mf": is_mf,
        "zone": zone,
        "details": details,
        "input_parameters": input_parameters,
        "geometry_details": {},
        "dev_scenarios": dev_scenarios_dict,
        "parcel": parcel.model,
    }
    if dry_run:
        # dry-run -- create analyzed listing object but don't save it to DB, and bail out of function
        a = AnalyzedListing(**al_defaults)
        a.listing = property_listing
        return a
    a: AnalyzedListing
    created: bool
    a, created = AnalyzedListing.objects.update_or_create(listing=property_listing, defaults=al_defaults)
    # Salt for hashing filenames in R2 (or S3) buckets.
    # Only upload images if there's a new salt since they don't typically change.
    salt = 0
    if not created:
        salt = a.salt
    if not salt or force_uploads:
        # either it's newly created, didn't have a salt entry, or re-upload images.
        if not salt:
            a.salt = secrets.token_urlsafe(10)
        salt = a.salt
        a.save(update_fields=["salt"])
        save_and_upload_figures(
            new_buildings_fig,
            cant_build_fig,
            split_lot_fig,
            salt,
            save_dir,
            apn,
            parcel.model.address,
            messages,
            save_to_cloud=True,
        )
    else:
        log.debug(f"Reusing salt and images for {parcel.model.address}")
    return a


def analyze_batch(
    parcels: list[Parcel],
    utm_crs: pyproj.CRS,
    property_listings: list[PropertyListing],
    dry_run: bool,
    save_dir: str,
    limit: int = None,
    try_split_lot: bool = True,
    single_process: bool = False,
) -> (list[AnalyzedListing], list[AnalyzedListing]):
    from lib.parallel_worker import analyze_one_parcel_worker

    """
    Notable arguments:
        property_listings: a list of listings of same length as parcels. Maps each
        dry_run: if True, don't save anything to filesystem or DB
        parcel to a listing to save, if preferred
    """
    # Format save_dir properly
    save_dir = os.path.join(save_dir, "")

    # Make folders if they don't exist
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    if not os.path.isdir(os.path.join(save_dir, "new-buildings")):
        os.makedirs(os.path.join(save_dir, "new-buildings"))
    if not os.path.isdir(os.path.join(save_dir, "lot-splits")):
        os.makedirs(os.path.join(save_dir, "lot-splits"))
    if not os.path.isdir(os.path.join(save_dir, "cant-build")):
        os.makedirs(os.path.join(save_dir, "cant-build"))

    num_analyze = min(len(parcels), int(limit)) if limit else len(parcels)

    log.info(f"Found {len(parcels)} parcels. Analyzing {num_analyze}.")

    assert property_listings is not None
    n_jobs = 1 if single_process else 8
    log.info(f"Launching {n_jobs} process for analysis...")

    if n_jobs == 1:
        results = [
            analyze_one_parcel_worker(
                parcels[i],
                utm_crs,
                property_listings[i],
                dry_run,
                save_dir=save_dir,
                try_split_lot=try_split_lot,
                i=i,
            )
            for i in range(num_analyze)
        ]
    else:
        results = Parallel(n_jobs=n_jobs)(
            delayed(analyze_one_parcel_worker)(
                parcels[i],
                utm_crs,
                property_listings[i],
                dry_run,
                save_dir=save_dir,
                try_split_lot=try_split_lot,
                i=i,
            )
            for i in range(num_analyze)
        )

    analyzed = [x[0] for x in results if x[0] is not None]
    errors = [x[1] for x in results if x[1] is not None]
    log.info(f"Done analyzing {num_analyze} parcels. {len(errors)} errors")
    return analyzed, errors
