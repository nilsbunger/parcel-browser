from statistics import NormalDist

from pydantic import BaseModel
import requests

from mygeo.settings import env
from world.models import Parcel, PropertyListing
from world.models.base_models import RentalUnit
from world.models.rental_data import RentalData


class RentService:
    def __init__(self):
        self.api_key = env('RENTOMETER_API_KEY')

        # output = {'address': None, 'latitude': '32.73427', 'longitude': '-117.169698', 'bedrooms': 2,
        #           'baths': '1 only', 'building_type': 'Any', 'look_back_days': 365, 'mean': 2915,
        #           'median': 2850, 'min': 1800, 'max': 4300, 'percentile_25': 2363, 'percentile_75': 3466,
        #           'std_dev': 817, 'samples': 12, 'radius_miles': 0.5,
        #           'quickview_url': 'https://www.rentometer.com/analysis/2-bed/32-73427-117-169698/oYsi8otxrsY/quickview',

    def rent_for_location(self, listing: PropertyListing, units: [RentalUnit], percentile: int, is_adu=False,
                          cache_only=True) -> int:
        """ Get the forecast rent for actual units or a hypothetical ADU at a location, and cache it.

        :param PropertyListing listing: MLS property listing to get rents for
        :param [RentalUnit] units: if set, return the value for an ADU of adu_unit at the location
        :param int percentile: what percentile we expect this property to rent for relative to mean rent
        :param bool is_adu: is this an ADU calculation (meaning it's not an 'actual' unit in the building
        :param bool cache_only:
        :return [int]: Rent for units in this listing, or for the hypothetical ADU rental type
        :rtype:
        """
        assert (percentile < 100)
        rent_cache = {}
        rents = []
        centroid = listing.parcel.geom.centroid
        (long, lat) = centroid.coords
        data_type = RentalData.RentalDataType.ADU_RENTOMETER_ESTIMATE if is_adu else RentalData.RentalDataType.UNIT_RENTOMETER_ESTIMATE

        # check for exact match in DB in case we've already done this parcel
        rd_list_for_parcel = list(RentalData.objects.filter(parcel=listing.parcel))
        if not is_adu and (listing.parcel.br < 1 or listing.parcel.ba < 1):
            print(f"Skipping {listing.addr} because there's no info on # of BR or BA")
            return -1
        for unit in units:
            # check if we already have this unit result in our array...
            if unit in rent_cache:
                rents.append(round(rent_cache[unit]))
                continue
            # ... or in the DB
            x = [r for r in rd_list_for_parcel if r.br == unit.br and r.ba == unit.ba]
            assert (len(x) < 2)
            if len(rd_list_for_parcel) and not len(x):
                print("HUH CHECK IT")
            # assert (len(x) or not len(rd_list_for_parcel))
            if not len(x) and cache_only:
                print(f"Skipping {unit.br}BR, {unit.ba}BA at {listing.addr},"
                      f"cache miss in cache-only mode")
                return []
            if len(x):
                rd = x[0]
            else:
                print(f"CALLING Rentometer: {listing.addr}, {unit.br}BR,{unit.ba}BA")
                output = self._call_rentometer(lat, long, unit.br, unit.ba)
                rd = RentalData(parcel=listing.parcel, br=output['bedrooms'], ba=output['baths'], sqft=None,
                                details=output, location=centroid, data_type=data_type)
                rd.save()
                rd_list_for_parcel.append(rd)
            rent_cache[unit] = -1
            if rd.details['samples'] >= 10:
                dist = NormalDist(mu=rd.details['mean'], sigma=rd.details['std_dev'])
                maybe_rent = dist.inv_cdf(percentile / 100.0)
                if maybe_rent < rd.details['max']:
                    rent_cache[unit] = maybe_rent
            if rent_cache[unit] == -1:
                # we didn't manage to assign a rent using the normal distribution, so fall back to a linear model
                assert (percentile >= 50)
                if percentile > 75:
                    rent_cache[unit] = rd.details['percentile_75'] + (
                                (percentile - 75) * (rd.details['max'] - rd.details['percentile_75'])) / 25
                else:
                    rent_cache[unit] = rd.details['mean'] + (
                                (percentile - 50) * (rd.details['percentile_75'] - rd.details['mean'])) / 25
            assert (rent_cache[unit] < rd.details['max'])
            rents.append(round(rent_cache[unit]))
        return rents

    def _call_rentometer(self, lat, long, br, ba):
        # TODO : remove extra junk fields from stuff being saved in rentaldata
        q = dict({
            'latitude': lat,
            'longitude': long,
            'bedrooms': br,
            'baths': "1" if ba == 1 else "1.5+",
            'api_key': self.api_key
        })
        r = requests.get('https://www.rentometer.com/api/v1/summary', params=q)
        r.raise_for_status()
        output = r.json()
        output['baths'] = 1 if output['baths'] == '1 only' else 2
        return output
