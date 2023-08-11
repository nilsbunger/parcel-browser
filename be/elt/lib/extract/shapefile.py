from datetime import date
import sys
import tempfile
import zipfile
from pathlib import Path, PosixPath
from pprint import pformat, pprint

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping, mapping, ogrinspect
from django.db.models import Count, Q
from django.contrib.gis.db import models


from elt.models import RawGeomData
import elt.models as elt_models
from elt.lib.elt_utils import (
    H3LayerMapping,
    elt_model_with_custom_save,
    elt_model_with_run_date,
    get_elt_file_assets,
    inspect_shapefile,
    pipestage_prompt,
)
from elt.lib.types import GisData, Juri

mapping = {
    "phase_1_A_20230727": {
        "geom": "MULTIPOLYGON",
        "data": ["mapblklot", "zoning", "height", "gen_hght", "DAG188", "DAG189"],
    },
    "phase_1_B_20230727": {
        "geom": "MULTIPOLYGON",
        "data": ["mapblklot", "zoning", "height", "gen_hght", "DAG199", "DAG200"],
    },
    "fourplex_for_1_A": {
        "geom": "MULTIPOLYGON",
        "data": ["mapblklot", "zoning", "height", "gen_hght", "FOURPLEX"],
    },
    "fourplex_for_1_B": {
        "geom": "MULTIPOLYGON",
        "data": ["mapblklot", "zoning", "height", "gen_hght", "FOURPLEX"],
    },
    "unknown": {
        "geom": "MULTIPOLYGON",
    },
}


def check_existing_db_data(geo: Juri, resolved_datatype: str, shapefilepaths: list[Path]):
    """Check for existing data in the database for a given date, for generic shapefile data (RawGeomData).
     This table has a convention that 'LAYER' and 'FILENAME' are used to identify the source of the data.
     Prompt user whether to overwrite it. Delete old data if user chooses to overwrite.

    Returns:
        user intention ('c' for create, 's' for skip, ...)
    """
    shptuples = [(DataSource(shp, encoding="utf-8"), shp.name) for shp in shapefilepaths]
    layers = [{"layer_name": ds[0].name, "shapefile": fname} for ds, fname in shptuples]
    q_objects = [Q(data__LAYER=val["layer_name"], data__FILENAME=val["shapefile"]) for val in layers]
    final_q = q_objects[0]
    for q in q_objects[1:]:
        final_q |= q

    datatype_obj_count = RawGeomData.objects.filter(juri=geo.value, data_type=resolved_datatype).count()
    matching_objects = RawGeomData.objects.filter(final_q).filter(juri=geo.value, data_type=resolved_datatype)
    unique_dates_with_counts = (
        matching_objects.values_list("run_date")  # Group by the date_field
        .annotate(count=Count("run_date"))  # Count the number of occurrences for each date
        .order_by("run_date")  # Optional: sort by the date
    )
    print("Existing data: ")
    [pprint(f"{date}: {count}") for date, count in unique_dates_with_counts]
    print(f"... out of {datatype_obj_count} w/ matching geo and datatype...")
    user_intent = pipestage_prompt(is_incremental=False, num_existing_entries=matching_objects.count())
    if user_intent == "c":
        print(
            f"Deleting matching {matching_objects.count()} entries out of {datatype_obj_count} w/ geo and datatype..."
        )
        matching_objects.delete()
    return user_intent


def extract_from_shapefile_generic(geo: Juri, resolved_datatype: str, zipfname: PosixPath, data_date: date):
    """Extract from one shapefile.zip to the generic RawGeomData model. Supports multiple .shp files in the zip"""
    print(f"Extract from shapefile to generic: geo={geo}, resolved_datatype={resolved_datatype}, zipfile={zipfile}")
    assert zipfname.suffix == ".zip"

    with tempfile.TemporaryDirectory() as tempdir:
        zf = zipfile.ZipFile(zipfname)
        shapefiles = [x for x in zf.namelist() if x.endswith(".shp")]
        shapefilepaths = [Path(tempdir, shapefile) for shapefile in shapefiles]
        zf.extractall(path=tempdir)

        user_intent = check_existing_db_data(geo, resolved_datatype, shapefilepaths)
        if user_intent == "s":
            print("Skipping stage")
            return
        assert user_intent == "c"

        for shapefile in shapefiles:
            shppath = Path(tempdir, shapefile)
            print("Extracting from shapefile: ", shapefile)

            # display shapefile metadata (optional)
            # inspect_shapefile(Path(tempdir, shapefile))

            ds = DataSource(shppath, encoding="utf-8")
            assert len(ds) == 1, "Expected only one layer in shapefile"

            def custom_save(self, *args, **kwargs):
                self.run_date = data_date
                self.juri = geo.value
                self.data_type = resolved_datatype
                self.data["LAYER"] = ds[0].name
                self.data["FILENAME"] = shapefile

            RawGeomModel = elt_model_with_custom_save("RawGeomData", custom_save)
            try:
                layer_map = mapping[ds[0].name]
            except KeyError:
                print("No mapping found for layer: ", ds[0].name)
                inspect_shapefile(shppath)
                lm = H3LayerMapping(RawGeomModel, shppath, mapping["unknown"], transform=True, using="default")
                lm.stats()
                print("Add mapping for the above fields")
                sys.exit(1)

            # fields in the layer: ['OBJECTID', 'mapblklot', 'zoning', 'height', 'gen_hght', 'DAG188', 'DAG189', 'Shape_Leng', 'Shape_Area']
            lm = H3LayerMapping(RawGeomModel, shppath, layer_map, transform=True, using="default")
            lm.stats()
            lm.save(strict=False, verbose=False, progress=True, step=500)  # fid_range=(0, 20))  # TODO: HACK!
            print("DONE")


def extract_from_shapefile_bespoke(geo: Juri, datatype: GisData, file_assets=None):
    """
    Extract data from shapefile, and update DB. Shapefile should be date-named and
    in geo/datatype_<anything> subdirectory.
    Write to / update DB model with name raw_<geo>_<datatype>.

    Args:
        geo (elt.lib.types.Juri): Which city / jurisdiction to extract data for.
        datatype (elt.lib.types.GisData): What type of data to extract. (e.g. "zoning", "parcels", etc.)
    Returns:
        None:
    """
    # model_missing = False
    # db_model = None
    print(f"Extract from shapefile: geo={geo}, gis_data_type={datatype}, file_assets={file_assets}")
    if not file_assets:
        file_assets = get_elt_file_assets(geo, datatype, None, extension="zip", expect_existing=True)
    latest_file = file_assets.latest_files[0]
    print(" Using latest file: ", latest_file)
    # date_from_filename = date_parse(latest_file.stem.split("_")[0], yearfirst=True).date()
    model_name = f"raw_{geo.value}_{file_assets.datatype}"
    model_name_camel = "".join(x.capitalize() for x in model_name.split("_"))
    # Wrap DB model with run_date method (also checking for db_model existence)
    db_model = elt_model_with_run_date(model_name_camel, file_assets.data_date)
    mapper = elt_models.__dict__[f"{model_name}_mapping"]

    with tempfile.TemporaryDirectory() as tempdir:
        zf = zipfile.ZipFile(latest_file)
        shapefiles = [x for x in zf.namelist() if x.endswith(".shp")]
        assert len(shapefiles) == 1
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
        ds = DataSource(Path(tempdir, shapefiles[0]))  # noqa:F841

        lm = LayerMapping(db_model, Path(tempdir, shapefiles[0]), mapper, transform=True, using="default")
        print(f"Deleting old data from DB {db_model}...")
        db_model.objects.all().delete()
        print(f"Saving data from {latest_file} to DB {db_model}...")
        # save new layer, with commit every 'step' entries.
        lm.save(strict=False, verbose=False, progress=True, step=500)
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
