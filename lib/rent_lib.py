import logging
from statistics import NormalDist
from typing import List

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
import requests
from requests import HTTPError

from mygeo.settings import env
from world.models import PropertyListing
from world.models.base_models import RentalUnit
from world.models.rental_data import RentalData

log = logging.getLogger(__name__)


class RentService:
    def rent_for_location(
        self,
        listing: PropertyListing,
        units: [RentalUnit],
        messages: any,
        dry_run: bool,
        percentile: int,
        interpolate_distance: int,
        is_adu=False,
    ) -> List[int]:
        """Get the forecast rent for actual units or a hypothetical ADU at a location, and cache it.

        :param PropertyListing listing: MLS property listing to get rents for
        :param [RentalUnit] units: if set, return the value for an ADU of adu_unit at the location
        :param any messages:
        :param bool dry_run: if True, don't make any changes to the database
        :param int percentile: what percentile we expect this property to rent for relative to mean rent
        :param bool is_adu: is this an ADU calculation (meaning it's not an 'actual' unit in the building
        :param int interpolate_distance: distance in meters to interpolate rents from before resorting to API call.
        :return [int]: Rent for units in this listing, or for the hypothetical ADU rental type
        """
        assert percentile < 100
        rent_cache = {}
        rents = []
        # check for exact match in DB in case we've already done this parcel
        if not is_adu and (listing.parcel.br < 1 or listing.parcel.ba < 1):
            log.info(
                f"Skipping {listing.addr}, APN={listing.parcel.apn} because there's no info on # of BR or BA"
            )
            messages["warning"].append(f"Missing rent: No info on # of BR or BA")

            return []
        rd_list_for_parcel = list(RentalData.objects.filter(parcel=listing.parcel))
        for unit in units:
            check_br = min(unit.br, 4)  # more than 4 BR is recorded as 4BR
            check_ba = min(unit.ba, 2)  # more than 2 BA is recorded as 2BA
            assert check_br > 0
            assert check_ba > 0
            # check if we already have this unit result in our array...
            if unit in rent_cache:
                rents.append(round(rent_cache[unit]))
                messages["stats"]["rent_from_memory_cache"] += 1
                continue
            # ... or in the DB
            x = [r for r in rd_list_for_parcel if r.br == check_br and r.ba == check_ba]
            assert (
                len(x) <= 1
            ), f"Multiple entries in RentalData for the same unit for APN={listing.parcel.apn}"
            if len(x):
                rd = x[0]
                messages["stats"]["rent_from_db"] += 1
            else:
                # no match for rent in memory cache or DB... try interpolating rent from nearby parcels
                tmp_rent = self.interpolate_rent_for_location(
                    listing, interpolate_distance, check_br, check_ba, messages, percentile
                )
                if tmp_rent > -1:
                    messages["stats"]["rent_interpolated"] += 1
                    rent_cache[unit] = tmp_rent
                    rents.append(round(rent_cache[unit]))
                    continue
                # couldn't interpolate rent... time to use an API credit
                messages["stats"]["rent_rentometer_call"] += 1
                log.info(f"CALLING Rentometer: {listing.addr}, {check_br}BR,{check_ba}BA")
                rd = self._get_rental_data_from_rentometer(
                    listing, check_br, check_ba, dry_run, is_adu=is_adu
                )
                rd_list_for_parcel.append(rd)
            tmp_rent = self._calculate_rent_from_rentdata_instance(rd, messages, percentile)
            if tmp_rent == -1:
                # Failed API call => bail on this whole listing
                log.info(
                    f"Skipping {unit.br}BR, {unit.ba}BA at {listing.addr}, mlsid={listing.mlsid},"
                    f"cached error from last time: code={rd.details['status_code']}, {rd.details['errors']}"
                )
                return []
            rent_cache[unit] = tmp_rent
            rents.append(round(rent_cache[unit]))
        return rents

    def interpolate_rent_for_location(
        self,
        listing: PropertyListing,
        interpolate_distance: int,
        check_br: int,
        check_ba: int,
        messages,
        percentile: int,
    ) -> int:
        """Interpolate rent from nearby parcels, with a max distance of interpolate_distance in meters."""
        loc = listing.parcel.geom.centroid
        near_rental_data = (
            RentalData.objects.filter(
                br=check_br, ba=check_ba, location__distance_lte=(loc, D(m=interpolate_distance))
            )
            .annotate(distance=Distance("location", loc))
            .order_by("distance")[0:19]
        )
        if len(near_rental_data) == 0:
            return -1
        # TODO: This isn't real interpolation... we literally just return the closest match within our distance limit
        return self._calculate_rent_from_rentdata_instance(
            near_rental_data[0], messages, percentile
        )

    def _calculate_rent_from_rentdata_instance(
        self, rd: RentalData, messages, percentile: int
    ) -> int:
        """Use the data in a RentalData instance to calculate the rent for a given percentile"""
        rent = -1
        # "rd" object either came from the DB or was created with an API call. Either way it can still have an error
        if rd.details.get("status_code") == 402:
            messages["error"].append("Missing rent: Rentometer API limit exceeded")
            log.critical(
                "No credits available from Rentometer. Please buy more credits, then "
                "run './manage.py rent_data reset_credits'"
            )
            return -1
        if rd.details.get("status_code", 200) != 200:
            messages["warning"].append(
                f"Missing rent: Rental data (live or from DB) has non-200 error code"
            )
            return -1

        # Ridiculous patch-up required -- 75th percentile is sometimes higher than max from rentometer??
        if rd.details["percentile_75"] > rd.details["max"]:
            rd.details["percentile_75"] = rd.details["max"] - 100
        if rd.details["samples"] >= 10:
            dist = NormalDist(mu=rd.details["mean"], sigma=rd.details["std_dev"])
            maybe_rent = dist.inv_cdf(percentile / 100.0)
            if maybe_rent < rd.details["max"]:
                rent = maybe_rent
        if rent == -1:
            # we didn't manage to assign a rent using the normal distribution, so fall back to a linear model
            assert percentile >= 50
            if percentile > 75:
                rent = (
                    rd.details["percentile_75"]
                    + ((percentile - 75) * (rd.details["max"] - rd.details["percentile_75"])) / 25
                )
            else:
                rent = (
                    rd.details["mean"]
                    + ((percentile - 50) * (rd.details["percentile_75"] - rd.details["mean"])) / 25
                )
        assert rent < rd.details["max"]
        return rent

    def _get_rental_data_from_rentometer(
        self, listing: PropertyListing, br: int, ba: int, dry_run, is_adu
    ) -> RentalData:
        """Make a call to Rentometer, record the results in our DB, and return a RentalData model instance"""
        centroid = listing.parcel.geom.centroid
        (long, lat) = centroid.coords
        data_type = (
            RentalData.RentalDataType.ADU_RENTOMETER_ESTIMATE
            if is_adu
            else RentalData.RentalDataType.UNIT_RENTOMETER_ESTIMATE
        )

        try:
            # Call Rentometer, or if in dry_run mode, just return a dummy object
            output = (
                self._call_rentometer(lat, long, br, ba)
                if not dry_run
                else self._dry_run_resp(br, ba)
            )
        except HTTPError as e:
            # create error output and save it as a rental data object
            log.error(
                f"  ERROR - {listing.addr} - APN={listing.parcel_id}: RENTOMETER FAILED WITH ERROR",
                str(e),
            )
            output = e.response.json()  # creates 'errors' key
            output.update(
                {
                    "bedrooms": br,
                    "baths": ba if ba < 2 else 2,
                    "status_code": e.response.status_code,
                }
            )
        rd = RentalData(
            parcel=listing.parcel,
            br=output["bedrooms"],
            ba=output["baths"],
            sqft=None,
            details=output,
            location=centroid,
            data_type=data_type,
        )
        if not dry_run:
            rd.save()
        return rd

    def _call_rentometer(self, lat, long, br, ba):
        q = dict(
            {
                "latitude": round(lat, 8),
                "longitude": round(long, 8),
                "bedrooms": br,
                "baths": "1" if ba == 1 else "1.5+",
                "api_key": env("RENTOMETER_API_KEY"),
            }
        )
        r = requests.get("https://www.rentometer.com/api/v1/summary", params=q)
        r.raise_for_status()
        output = r.json()
        output["baths"] = 1 if output["baths"] == "1 only" else 2
        # remove extra junk fields
        del output["links"]
        del output["quickview_url"]
        return output

    def _dry_run_resp(self, br, ba):
        log.info("  DRY RUN - Rentometer API call would have been made here")
        # Example output from _call_rentometer_functtion:
        return {
            "address": None,
            "latitude": "32.73427",
            "longitude": "-117.169698",
            "bedrooms": br,
            "baths": ba if ba < 2 else 2,
            "building_type": "Any",
            "look_back_days": 365,
            "mean": 2915,
            "median": 2850,
            "min": 1800,
            "max": 4300,
            "percentile_25": 2363,
            "percentile_75": 3466,
            "std_dev": 817,
            "samples": 12,
            "radius_miles": 0.5,
        }
