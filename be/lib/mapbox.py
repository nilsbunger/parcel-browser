import logging
import urllib
from datetime import UTC, datetime, timedelta

import requests
from parsnip.settings import env

MAPBOX_API_KEY = env("MAPBOX_API_KEY")  # noqa: N806
assert MAPBOX_API_KEY

log = logging.getLogger(__name__)

STATE_ABBREVIATIONS = {
    "California": "CA",
    # ... Add more as needed
}


class AddressNormalizer:
    """Accept an address string and normalize it using the Mapbox API"""

    params = {"access_token": MAPBOX_API_KEY}

    def __init__(self, street_addr, city="", state="", zip=""):
        """Street_addr can either be a full address or just a street address."""
        self._orig_street_addr = street_addr
        self._orig_city = city
        self._orig_state = state
        self._orig_zip_code = zip
        self._full_address = street_addr
        if city:
            self._full_address += f", {city}"
        if state:
            self._full_address += f", {state}"
        if zip:
            self._full_address += f" {zip}"

        self._normalize_address()

    def _normalize_address(self):
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(self._full_address)}.json"
        log.info("Making Mapbox API request for address resolution")
        response = requests.get(url, params=self.params)
        self._data = response.json()

        if not self._data["features"]:
            return None

        # The API returns a list of possible matches, sorted by relevance. The first is what we want.
        self._feature = self._data["features"][0]
        placetype: list = self._feature["place_type"]
        placename = self._feature["place_name"]
        if "address" not in placetype:  # no exact address match
            return None
        street, self.city, statezip, self.country = placename.split(", ")
        *state, self.zip = statezip.split(" ")
        self.state = " ".join(state)
        self.state = STATE_ABBREVIATIONS[self.state]
        self.streetnum, *rest = street.split(" ")
        self.streetname = " ".join(rest)
        self.full_address = placename


# Mapbox tokens have to be periodically rotated if they're exposed to the client. This function
# creates a temporary token that expires in 1 hour.
def get_temporary_mapbox_token():
    url = "https://api.mapbox.com/tokens/v2/nilshome3"
    headers = {"Content-Type": "application/json"}

    payload = {
        "expires": (datetime.now(tz=UTC) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scopes": [
            "styles:read",
            "styles:tiles",
            "fonts:read",
            "datasets:read",
            "vision:read",
        ],
    }

    response = requests.post(
        url,
        params={"access_token": MAPBOX_API_KEY},
        headers=headers,
        json=payload,
    )

    if response.status_code == 201:
        return response.json().get("token")
    else:
        print(f"Error creating temporary token: {response.status_code}")
        return None


if __name__ == "__main__":
    address = "1234 W main st apt 5b"
    address = "500 funston ave"
    address = "1835 7th Street NW #231"
    city = "Washington, DC"
    # city = "San Francisco"
    # state = "CA"
    # zip_code = "94103"
    norm_addr = AddressNormalizer(address, city)

    print(norm_addr)
