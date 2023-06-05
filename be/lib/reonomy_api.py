import ast
from collections import Counter
from datetime import datetime
from math import ceil
from pprint import pformat

import requests

REONOMY_ACCESS_KEY = "home3inc"
REONOMY_SECRET_KEY = "e6ey32vyrghuuag9"

# Authorization: Basic aG9tZTNpbmM6ZTZleTMydnlyZ2h1dWFnOQ=="

url_base = "https://api.reonomy.com/v2/"
headers = {
    "Authorization": f"Basic aG9tZTNpbmM6ZTZleTMydnlyZ2h1dWFnOQ==",
    "Content-Type": "application/json",
}


def reonomy_call(api_call, method, params=None, body=None, save=True):
    url = url_base + api_call
    if method == "GET":
        response = requests.get(url, params=params, json=body, headers=headers)
    elif method == "POST":
        response = requests.post(url, params=params, json=body, headers=headers)
    else:
        raise ValueError(f"Invalid method: {method}")
    if response.status_code != 200:
        print("ERROR: ", response.status_code)
        return None
    else:
        response = response.json()
        if save:
            save_resp(response, api_call)
        return response


def reonomy_get_call(api_call, params=None, body=None, save=True):
    return reonomy_call(api_call, "GET", params, body, save)


def reonomy_post_call(api_call, params=None, body=None, save=True):
    return reonomy_call(api_call, "POST", params, body, save)


def save_resp(response, api_call):
    time_str = datetime.now().strftime("%m%d %H:%M:%S")
    with open("reonomy_calls.py", mode="a") as localfile:
        localfile.write('\n["' + time_str + ": " + api_call + '",\n' + pformat(response, indent=2) + "],")


def reonomy_search_summary_call(all=False, save=True):
    # get list of properties matching a filtered search
    body = {
        "bounding_box": {},
        "settings": {
            # "building_area": {"min": 5000},
            # "neighborhood": ["Richmond"], # TODO: unclear if this is a valid field
            # fmt:off
            "land_use_code": ["106", "113", "131", "132", "133", "236", "1100", "1104", "1105", "1106", "1107",
                              "1110", "1112","9217","111","1005","119","155","1108","1113","151","1103","157","9106",
                              ],
            # fmt:on
            "locations": [{"kind": "city", "state": "CA", "text": "San Francisco"}],
            "portfolio_properties_count": {"max": 10},
            "total_units": {"max": 50, "min": 10},
        },
    }
    resp = reonomy_post_call("search/summaries", body=body, save=save)
    num_pages = ceil(resp["count"] / 10)
    if (not all) and (num_pages > 1):
        print("WARNING: only returning first page of results out of resp['count'] results")
        return resp
    accum_resp = resp
    # Query all pages as per https://api.reonomy.com/v2/docs/guides/search/#pagination
    for page in range(2, num_pages + 1):
        print("page", page)
        page_params = {"search_token": resp["search_token"]}
        resp = reonomy_post_call("search/summaries", body=body, params=page_params, save=save)
        accum_resp["items"].extend(resp["items"])
    return accum_resp


def read_saved_calls() -> list[list[str, dict]]:
    with open("reonomy_calls.py", mode="r") as localfile:
        lines = localfile.readlines()
    lines[-1] += "]"
    try:
        saved_calls = ast.literal_eval("".join(lines))
    except ValueError as e:
        print(e)
    print("DONE")
    return saved_calls


def find_search_summaries(saved_calls):
    search_summary_calls = [call[1] for call in saved_calls if "search/summaries" in call[0]]

    # merge search_summary_calls from multiple calls into a single list of all properties (may contain dupes)
    search_summaries = []
    for call in search_summary_calls:
        search_summaries.extend(call["items"])

    # create a dictionary indexed by 'id' of the search summaries, noting and removing duplicates
    id_dict = {}
    for summary in search_summaries:
        id = summary["id"]
        if id in id_dict:
            print(f"WARNING: duplicate id {id}")
        id_dict[id] = summary

    num_dupes = len(search_summaries) - len(id_dict)
    print(f"DONE. Found {num_dupes} duplicates.")

    # Create a histogram of the master_update_time field (which is a date) across all the properties in id_dict
    # This is a proxy for the date the property was last updated
    dates = [id_dict[id]["sale_update_time"] for id in id_dict]
    hist = Counter(dates)

    sold_may_26 = [id for id in id_dict if id_dict[id]["sale_update_time"] == "2023-05-26"]
    print(f"Found {len(sold_may_26)} properties sold on May 26, 2023")
    assert len(sold_may_26) == 1
    # reonomy_property_detail_call(sold_may_26[0], save=True)

    return id_dict


def reonomy_property_detail_call(id, save=True):
    # Caution -- This call uses up one of our precious tokens!
    resp = reonomy_get_call(
        f"property/{id}",
        params={
            "detail_type": ["taxes", "sales", "mortgages", "basic", "reported-owners", "tenants", "ownership"],
            "filter_pii": False,
        },
        save=save,
    )
    return resp


def main():
    saved_calls = read_saved_calls()
    find_search_summaries(saved_calls)

    # resp = reonomy_get_call("users/me", save=False)
    # resp = reonomy_search_summary_call(all=False, save=False)
    # ids = [x["id"] for x in resp["items"]]

    # EXPENSIVE CALL:
    # for id in ids[2:6]:
    #     print(id)
    #     resp = reonomy_property_detail_call(id, save=True)
    print("DONE")


if __name__ == "__main__":
    main()
