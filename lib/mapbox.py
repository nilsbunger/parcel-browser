from datetime import datetime, timedelta, timezone

import requests

from mygeo.settings import env


# Mapbox tokens have to be periodically rotated if they're exposed to the client. This function
# creates a temporary token that expires in 1 hour.
def get_temporary_mapbox_token():
    MAPBOX_API_KEY = env("MAPBOX_API_KEY")  # noqa: N806
    assert MAPBOX_API_KEY
    url = "https://api.mapbox.com/tokens/v2/nilshome3"
    headers = {"Content-Type": "application/json"}

    payload = {
        "expires": (datetime.now(tz=timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
