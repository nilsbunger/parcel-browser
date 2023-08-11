from elt.lib.elt_utils import get_elt_file_assets
from elt.lib.extract.shapefile import extract_from_shapefile_bespoke, extract_from_shapefile_generic
from elt.lib.types import GisData, Juri


def extract_autodetect(geo: Juri, datatype: GisData):
    """Extract latest data for a jurisdiction and data type, auto-detecting type of file.

    Right now this assumes that the destination is the generic model, but it could be adapted for bespoke
    models as well.
    """

    file_assets = get_elt_file_assets(geo, datatype, stage_subdir=None, expect_existing=True)
    print(" Using latest files: ", [str(f) for f in file_assets.latest_files])

    for f in file_assets.latest_files:
        if f.suffix == ".json":
            print("Extracting from JSON")
            # TODO : adapt this method to put into a generic data type
            raise NotImplementedError("Need to adapt extract_from_json to write to a generic model")
            # extract_from_json(geo, datatype)
        elif f.suffix == ".zip":
            print("Extracting from shapefile")
            extract_from_shapefile_generic(geo, file_assets.resolved_datatype, f, file_assets.data_date)
        else:
            raise NotImplementedError("Don't know how to extract from file: ", str(f))

    print(file_assets)
