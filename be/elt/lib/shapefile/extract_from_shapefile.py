from datetime import date
import sys
import tempfile
import zipfile
from pathlib import Path
from pprint import pformat

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping, mapping, ogrinspect

import elt.models as elt_models
from elt.lib.types import Juri, GisData
from elt.lib.elt_utils import get_elt_pipe_filenames, pipestage_prompt
from dateutil.parser import parse as date_parse


# Return a version of the DB model which sets the run-date as specified.
# this can likely become a mixin or an inheritance class for models with this property
def wrapped_db_model(model_name_camel: str, date_from_filename: date):
    raw_model = elt_models.__dict__[model_name_camel]

    # class WrappedDbModel(raw_model):
    def custom_save(self, *args, **kwargs):
        self.run_date = date_from_filename
        super(raw_model, self).save(*args, **kwargs)

    custom_save.__dict__["alters_data"] = True
    raw_model.save = custom_save
    return raw_model


# Extract data from shapefile, and update DB.
# Expect shapefile to exist as zip file in 0.shapefile/ subdirectory.
# Write to / update DB model with name raw_<geo>_<datatype>.
def extract_from_shapefile(geo: Juri, datatype: GisData, thru_data=None):
    model_missing = False
    db_model = None
    print(f"Extract from shapefile: geo={geo}, gis_data_type={datatype}")
    pipestage_dirname = "0.shapefile"
    existing_files, resolved_datatype, _ = get_elt_pipe_filenames(
        geo, datatype, pipestage_dirname, extension="zip", expect_existing=True
    )
    latest_file = existing_files[0]
    print(" Using latest shapefile: ", latest_file)
    date_from_filename = date_parse(latest_file.stem, yearfirst=True).date()
    zf = zipfile.ZipFile(latest_file)
    shapefile = [x for x in zf.namelist() if x.endswith(".shp")][0]
    # Check if DB model exists in our web app
    model_name = f"raw_{geo.name}_{resolved_datatype}"
    model_name_camel = "".join(x.capitalize() for x in model_name.split("_"))
    try:
        db_model = wrapped_db_model(model_name_camel, date_from_filename)
        # Found model - prompt user for intention - skip stage, incrementally update, or create new data?
        user_intention = pipestage_prompt(is_incremental=False, existing_filename="DB")
        if user_intention == "s":
            print("Skipping stage")
            return
    except KeyError:
        model_missing = True

    with tempfile.TemporaryDirectory() as tempdir:
        zf.extractall(path=tempdir)
        # Django model doesn't exist... generate text for it and exit.
        if model_missing:
            generate_model_text(tempdir, model_name)
            sys.exit(1)
        mapper = elt_models.__dict__[f"{model_name}_mapping"]
        ds = DataSource(Path(tempdir, shapefile))

        lm = LayerMapping(db_model, Path(tempdir, shapefile), mapper, transform=True, using="default")
        print(f"Deleting old data from DB {db_model}...")
        db_model.objects.all().delete()
        print(f"Saving data from {latest_file} to DB {db_model}...")
        # save new layer, with commit every 'step' entries.
        lm.save(strict=True, verbose=False, progress=True, step=500)
        print("Done saving.")


def generate_model_text(tempdir, model_name):
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
