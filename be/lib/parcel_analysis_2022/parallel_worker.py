import logging
from typing import TYPE_CHECKING

import django
import pyproj
from joblib import Parallel, delayed
from world.models import Roads

if TYPE_CHECKING:
    from world.models import Parcel, PropertyListing

log = logging.getLogger(__name__)
django.setup()


def analyze_road_batch(
    roads: list[Roads],
    utm_crs: pyproj.CRS,
    single_process=False,
):
    n_jobs = 1 if single_process else 2
    if n_jobs == 1:
        [analyze_road_worker(road, utm_crs) for road in roads]
    else:
        Parallel(n_jobs=n_jobs)(delayed(parallel_analyze_road_worker)(road, utm_crs) for road in roads)


def analyze_road_worker(road: Roads, utm_crs: pyproj.CRS):
    # print(f"Analyzing road {road.name}")
    # road.analyze(utm_crs)
    raise AssertionError("Not implemented yet... copy from co.py mgmt command")
    return road


def parallel_analyze_road_worker(*args, **kwargs):
    analyze_road_worker(*args, **kwargs)


def analyze_one_parcel_worker(
    parcel: "Parcel",
    utm_crs: pyproj.CRS,
    property_listing: "PropertyListing",
    dry_run: bool,
    save_dir: str,  # this used to have a default, but it shouldn't be used
    try_garage_conversion=True,
    try_split_lot=True,
    i: int = 0,
):
    from .analyze_parcel_lib import analyze_one_parcel

    assert property_listing is not None
    try:
        result = analyze_one_parcel(
            parcel,
            utm_crs,
            property_listing,
            dry_run,
            save_dir=save_dir,
            show_plot=False,
            try_garage_conversion=try_garage_conversion,
            try_split_lot=try_split_lot,
        )
        return result, None
    except Exception as e:
        # log.error()
        log.error(f"Exception on parcel {parcel.apn}", exc_info=True)
        # raise e
        return None, {
            "apn": parcel.apn,
            "error": e,
        }
