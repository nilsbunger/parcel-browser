import sys
import tempfile
import zipfile
from pathlib import Path
from pprint import pformat

from dateutil.parser import parse as date_parse
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping, mapping, ogrinspect
from django.db import models

import elt.models as elt_models
from elt.lib.elt_utils import elt_model_with_run_date, get_elt_pipe_filenames, pipestage_prompt
from elt.lib.types import GisData, Juri


def extract_from_shapefile(geo: Juri, datatype: GisData):
    """
    Extract data from shapefile, and update DB.Expect shapefile to exist as zip file in 0.shapefile/ subdirectory.
    Write to / update DB model with name raw_<geo>_<datatype>.

    Args:
        geo (elt.lib.types.Juri): Which city / jurisdiction to extract data for.
        datatype (elt.lib.types.GisData): What type of data to extract. (e.g. "zoning", "parcels", etc.)

    Returns:
        None:
    """
    # model_missing = False
    # db_model = None
    print(f"Extract from shapefile: geo={geo}, gis_data_type={datatype}")
    pipestage_dirname = "0.shapefile"
    existing_files, resolved_datatype, _ = get_elt_pipe_filenames(
        geo, datatype, pipestage_dirname, extension="zip", expect_existing=True
    )
    model_name = f"raw_{geo.name}_{resolved_datatype}"
    latest_file = existing_files[0]
    print(" Using latest file: ", latest_file)

    date_from_filename = date_parse(latest_file.stem.split("_")[0], yearfirst=True).date()
    model_name_camel = "".join(x.capitalize() for x in model_name.split("_"))
    # Check if DB model exists in our web app
    db_model = elt_model_with_run_date(model_name_camel, date_from_filename)

    with tempfile.TemporaryDirectory() as tempdir:
        zf = zipfile.ZipFile(latest_file)
        shapefile = [x for x in zf.namelist() if x.endswith(".shp")][0]
        zf.extractall(path=tempdir)
        if not db_model:
            # Django model doesn't exist yet... generate python code to add into django app and exit.
            generate_model_text_from_shapefile(tempdir, model_name)
            sys.exit(1)

        # Found model - prompt user for intention - skip stage, incrementally update, or create new data?
        user_intention = pipestage_prompt(is_incremental=False, existing_filename="DB")
        if user_intention == "s":
            print("Skipping stage")
            return
        assert user_intention == "c"

        # Save new data to DB from shapefile
        mapper = elt_models.__dict__[f"{model_name}_mapping"]
        ds = DataSource(Path(tempdir, shapefile))

        lm = LayerMapping(db_model, Path(tempdir, shapefile), mapper, transform=True, using="default")
        print(f"Deleting old data from DB {db_model}...")
        db_model.objects.all().delete()
        print(f"Saving data from {latest_file} to DB {db_model}...")
        # save new layer, with commit every 'step' entries.
        lm.save(strict=True, verbose=False, progress=True, step=500)
        print("Done saving.")


def generate_model_text_from_shapefile(tempdir, model_name):
    # Create new Django model text by inspecting extracted zip.
    model_name_camel = "".join(x.capitalize() for x in model_name.split("_"))
    new_model_py_code = ogrinspect(
        data_source=tempdir,
        model_name=model_name_camel,
        multi_geom=True,
        blank=True,
        null=True,
        srid=4326,
    )
    mappings = mapping(data_source=tempdir, geom_name="geom", layer_key=0, multi_geom=True)
    new_model_py_code += "\n    run_date = models.DateField()"
    print(new_model_py_code)
    print(f"\n{model_name}_mapping = {{\n {pformat(mappings, indent=4, compact=True)[1:]}")

    print(
        f"""
Add text above to elt/models/__init__.py and elt/models/{model_name}.py.
Then run './manage.py makemigrations' and './manage.py migrate'.
Then run this script again.
"""
    )
