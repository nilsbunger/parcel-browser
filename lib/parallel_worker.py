import logging
import django
import pyproj

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.models import Parcel, PropertyListing

log = logging.getLogger(__name__)
django.setup()


def parallel_analyze_road_worker(*args, **kwargs):
    from lib.analyze_road_lib import analyze_road_worker

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
    from lib.analyze_parcel_lib import analyze_one_parcel

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
