from dataclasses import dataclass

from pydantic import ValidationError

from elt.lib.ext_api.cacheable_api import CacheableApi
from elt.lib.ext_api.rentometer_types import RentometerResponse
from elt.models import ExternalApiData


@dataclass(kw_only=True)
class RentometerApi(CacheableApi):
    api_key: str
    api_url: str = "https://www.rentometer.com/api/v1/summary"
    vendor: ExternalApiData.Vendor = ExternalApiData.Vendor.RENTOMETER

    @property
    def headers(self):
        return {"Accept": "application/json"}

    def _single_data_fetcher(self, url: str, params: dict[str, any]) -> dict[str, any]:
        # get data for a single page, parsing the response as a single object. Used by comps API call.
        json_resp = self._fetch_json(url, params, self.headers)
        return json_resp

    def rent_for_location(self, lat: float, long: float, br: int, ba: int):  # -> RentometerResponse:
        params = dict(
            {
                "latitude": round(lat, 8),
                "longitude": round(long, 8),
                "bedrooms": br,
                "baths": "1" if ba == 1 else "1.5+",
                "api_key": self.api_key,
            }
        )
        hash_version = 1
        lookup_key = f"{lat},{long},{br},{ba}"
        external_data = self.get(self.api_url, params, lookup_key, hash_version, self._single_data_fetcher)
        try:
            rent_data = RentometerResponse.parse_obj(external_data.data)
        except ValidationError as e:
            print(e)
            print("...")
            raise e
        return rent_data
