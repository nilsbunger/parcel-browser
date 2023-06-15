# From SF PIM, get sales and building permits and other assessor info.

# TODO: this should be combined with arcgis extractor

import ast
from collections import Counter
from datetime import datetime
from pprint import pformat, pprint
from random import random
from time import sleep
from urllib.parse import urlencode

from dateutil.parser import parse
from parsnip.settings import env
from scraper_api import ScraperAPIClient

__url = (
    "https://sfplanninggis.org/proxy/DotNet/proxy.ashx?https://sfplanninggis.org/arcgiswa/rest/services/PIM_v26/MapServer/identify?"
    "f=json&tolerance=0&returnGeometry=false&returnFieldName=false&returnUnformattedValues=false&imageDisplay=613,742,96"
    '&geometry={"rings":[[[-13629815.5599,4548224.985600002],'
    "[-13629862.5301,4548217.433300003],"
    "[-13629865.3611,4548235.338600002],"
    "[-13629818.3977,4548242.935099997],"
    "[-13629815.5599,4548224.985600002]]]}"
    "&geometryType=esriGeometryPolygon&sr=102113"
    "&mapExtent=-13630029.73147821,4548000.514447921,-13629652.39345948,4548457.259651669"
    "&layers=all"
)
# WEBSITE with EPSG3857 coords: https://epsg.io/map#srs=3857&x=-13638000&y=4546000&z=13&layer=osm
# Sunset top left: -13638000 4546000
# Sunset top left: 37.7647, -122.5108, top right: 37.7684, -122.3813
# SF bottom left: 37.7076, -122.508

# SF max x (rightmost): -13624000
#     max y (topmost): 4553000
#    min x (leftmost): -13638000
#    min y (bottommost): 4538000
# ESRI code:
# ESRI:102113 - deprecated,replaced by 102100
#   Alternatives codes : 3857
# EPSG3857 - used by google maps. - https://epsg.io/3857

# API docs for this call:
# https://developers.arcgis.com/rest/services-reference/enterprise/identify-map-service-.htm

# General SFGIS server: https://sfplanninggis.org/arcgiswa/rest/services  -- note that PIM_v26 service requires proxy.

pim_base_url = "https://sfplanninggis.org/proxy/DotNet/proxy.ashx?https://sfplanninggis.org/"


def save_resp(fname, response, api_call):
    time_str = datetime.now().strftime("%m%d %H:%M:%S")
    with open(fname, mode="a") as localfile:
        localfile.write('\n["' + time_str + ": " + api_call + '",\n' + pformat(response, indent=2) + "],")


def sf_pim_base_params():
    return {
        "f": "json",
        "tolerance": 2,  # tolerance in pixels for where to run query
        "returnGeometry": False,
        "returnFieldName": False,
        "returnUnformattedValues": False,
        "imageDisplay": "800,600,96",
        "geometry": '{"rings":[[[-13629815.5599,4548224.985600002],'
        "[-13629862.5301,4548217.433300003],"
        "[-13629865.3611,4548235.338600002],"
        "[-13629818.3977,4548242.935099997],"
        "[-13629815.5599,4548224.985600002]]]}",
        "geometryType": "esriGeometryPolygon",
        "sr": "102113",
        "mapExtent": "-13630029.73147821,4548000.514447921,-13629652.39345948,4548457.259651669",
        "layers": "all:32",  # layer 32 is assessor layer.
        "layerDefs": "{\"32\": \"AssessorMulti_Project_USECODE IN ('A', 'A5', 'A15', 'DA', 'DA5', 'DA15', 'DCON', 'DD', 'DD5', 'F', 'F2', 'F15', 'FA', 'FA5', 'FS', 'FS5', 'FS15', 'OA', 'OA5', 'OA15', 'XV')\"}",
    }


# # Mapserver umbrella call -- gets lots of metadata for this service, including layer descriptions, tables, etc.
# params = {"f": "json"}
# api_call = "arcgiswa/rest/services/PIM_v26/MapServer"

# # Mapserver layer info call - https://developers.arcgis.com/rest/services-reference/enterprise/all-layers-and-tables.htm
# params = {"f": "json"}
# api_call = "arcgiswa/rest/services/PIM_v26/MapServer/layers"

## NEED TO ADD 4538000 to 4546000 to the Y coords range...


def sf_pim_call(save=True):
    api_call = "arcgiswa/rest/services/PIM_v26/MapServer/identify"
    errors = []
    success = []
    client = ScraperAPIClient(env("SCRAPER_API_KEY"))
    params = sf_pim_base_params()
    x_step = 1000
    y_step = 2000
    idx = 0
    for y in range(4538000, 4546000 - 1, y_step):
        # for y in range(4538000, 4553000 - 1, y_step):  TODO: FIX THE Y RANGE TO ENCOMPASS BOTH
        print("Y STEP")
        for x in range(-13638000, -13624000 - 1, x_step):
            idx += 1
            y2 = y + y_step
            x2 = x + x_step
            params["geometry"] = (
                '{"rings":[[' f"[{x2},{y}]," f"[{x},{y}]," f"[{x},{y2}]," f"[{x2},{y2}]," f"[{x2},{y}]]]}}"
            )

            url_to_scrape = pim_base_url + api_call + "?" + urlencode(params)
            response = client.get(url_to_scrape)
            if response.status_code != 200:
                print("ERROR: ", response.status_code)
                print(f"{x},{y}: ERROR ({response.status_code})")
                errors.append((x, y, response))
            else:
                response = response.json()
                success.append((x, y, response))
                print(f"{x},{y}: Found {len(response['results'])} matching results")
                if save:
                    save_resp(fname=str(y), response=response, api_call=api_call)
                # add random sleep to avoid getting blocked by server
            sleep(random() * 30)
    print("DONE")
    return response


def load_calls_from_disk() -> list[list[str, dict]]:
    fnames = ["4538000", "4540000", "4542000", "4544000", "4546000", "4548000", "4550000", "4552000"]
    # fnames = ["4546000", "4548000"]
    saved_calls = []
    for fname in fnames:
        print("Loading", fname)
        with open(fname) as localfile:
            lines = localfile.readlines()
        lines[0] = "[" + lines[0]
        lines[-1] += "]"
        try:
            raw_lines = ast.literal_eval("".join(lines))
            saved_calls.extend(raw_lines)
        except ValueError as e:
            print(e)
    l = [x[1]["results"] for x in saved_calls]
    flatlist = [item for sublist in l for item in sublist]
    print(f"DONE. Found {len(flatlist)} records")
    dates = [x["attributes"]["CURRSALEDATE"] for x in flatlist]
    dates = ["1970/1/1" if d == "Null" else d for d in dates]
    pprint(sorted(Counter([(parse(d).year, parse(d).month) for d in dates]).items()))
    return flatlist


def main():
    # sf_pim_call()
    multifam_list = load_calls_from_disk()


if __name__ == "__main__":
    main()
