from pathlib import Path
from pprint import pformat, pprint
import sys
import tempfile
import zipfile

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping, mapping, ogrinspect

from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum
from lib.extract.elt_utils import get_elt_pipe_filenames, pipestage_prompt
import elt.models as elt_models


# Extract data from shapefile, and update DB.
def extract_from_shapefile(geo: GeoEnum, datatype: GisDataTypeEnum, thru_data=None):
    model_missing = False
    db_model = None
    print(f"Extract from shapefile: geo={geo}, gis_data_type={datatype}")
    pipestage_dirname = f"0.shapefile"
    existing_files, _ = get_elt_pipe_filenames(
        geo, datatype, pipestage_dirname, extension="zip", expect_existing=True
    )
    latest_file = existing_files[0]
    print(" Using latest shapefile: ", latest_file)
    zf = zipfile.ZipFile(latest_file)
    shapefile = [x for x in zf.namelist() if x.endswith(".shp")][0]
    # Check if model exists
    model_name_underscored = f"raw_{geo.name}_{datatype.name}"
    model_name_camel = "".join(x.capitalize() for x in model_name_underscored.split("_"))
    try:
        db_model = elt_models.__dict__[model_name_camel]
    except KeyError as e:
        model_missing = True
    if not model_missing:
        # Prompt user for intention - skip stage, incrementally update, or create new data?
        user_intention = pipestage_prompt(is_incremental=False, existing_filename="DB")
        if user_intention == "s":
            print("Skipping stage")
            return
    with tempfile.TemporaryDirectory() as tempdir:
        zf.extractall(path=tempdir)
        if model_missing:
            new_model = ogrinspect(
                data_source=tempdir,
                model_name=model_name_camel,
                multi_geom=True,
                blank=True,
                null=True,
            )
            mappings = mapping(data_source=tempdir, geom_name="geom", layer_key=0, multi_geom=True)
            print(new_model)
            print(f"\n{model_name_underscored}_mapping = {{\n {pformat(mappings, indent=4, compact=True)[1:]}")

            print(f"\n\nAdd text above to elt/models/__init__.py and elt/models/{model_name_underscored}.py.")
            print("Then run './manage.py makemigrations' and './manage.py migrate'")
            sys.exit(1)
        mapper = elt_models.__dict__[f"{model_name_underscored}_mapping"]
        lm = LayerMapping(db_model, Path(tempdir, shapefile), mapper, transform=True, using="default")
        print("Deleting old data from DB {db_model}...")
        db_model.objects.all().delete()
        print(f"Saving data from {latest_file} to DB {db_model}...")
        lm.save(strict=True, verbose=False, progress=True)
        print("Done saving.")
