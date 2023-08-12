""" Extract data from a .json file into a Django model. """
import ast

from dateutil.parser import parse as date_parse

from elt.lib.elt_utils import get_elt_file_assets
from elt.lib.types import GisData, Juri


def extract_from_json(geo: Juri, datatype: GisData, thru_data=None):
    print(f"Extract from JSON: geo={geo.value}, data={datatype.value}")
    pipestage_dirname = "0.json"
    file_assets = get_elt_file_assets(geo, datatype, pipestage_dirname, extension="json", expect_existing=True)
    latest_file = file_assets.latest_files[0]
    print("Extracting from latest matching file: ", latest_file)
    date_from_filename = date_parse(  # noqa: F841 unused variable
        latest_file.stem.split("_")[0], yearfirst=True
    ).date()

    # load json from latest file

    with open(latest_file) as localfile:
        lines = localfile.readlines()
    lines[-1] += "]"
    try:
        saved_calls = ast.literal_eval("".join(lines))  # noqa: F841 unused variable
    except ValueError as e:
        print(e)
    print("DONE")
