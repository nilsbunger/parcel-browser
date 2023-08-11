from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Callable
import warnings
from copy import deepcopy
from datetime import date, datetime
from itertools import chain, islice
from zoneinfo import ZoneInfo
from dateutil.parser import parse as date_parse
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.gdal import DataSource, GDALException, OGRGeomType
from django.contrib.gis.utils import LayerMapError, LayerMapping
from django.core.exceptions import FieldDoesNotExist

from django.db import models
from django.db.models import JSONField
import pandas as pd
from rich.prompt import Prompt

from elt import models as elt_models
from elt.lib.types import GisData, Juri


def log_and_print(logmsg, log):
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    logmsg = f"{now.strftime('%y%m%d %H:%M:%S')}:: {logmsg}"
    log.write(logmsg)
    print(logmsg)


# Prompt user within a pipestage - do they want to create new data, add to existing data, or skip the stage?
# Returns 'c', 'i', or 's' for create, incremental, or skip
def pipestage_prompt(is_incremental, existing_filename=None, num_existing_entries=None, run_date=None):
    print("Stage options:")
    # print options for this stage. run_date and num_existing won't print if num_existing_entries is 0.
    num_existing_str = f" {num_existing_entries}" if num_existing_entries else ""
    fname_str = f" with data from {existing_filename}" if existing_filename else ""
    run_date_str = f" having run_date={run_date}" if run_date and num_existing_entries else ""
    assert not (run_date and not num_existing_entries)
    print(f"C:Create new data, replacing{num_existing_str} existing entries{fname_str}{run_date_str}")
    prompt_options = ["c", "s"]
    if is_incremental and (num_existing_entries or existing_filename):
        print(f"I:Add to{num_existing_str} existing entires incrementally{fname_str}{run_date_str}")
        prompt_options += ["i"]
    if num_existing_entries or existing_filename:
        print(f"S:Skip stage, using latest{num_existing_str} existing entries{fname_str}{run_date_str}")
    else:
        print("Note: no existing data found for this stage. Choosing C...")
        return "c"
    use_file = Prompt.ask("Your choice? ", choices=prompt_options)
    return use_file


def batched(iterable, n):
    """Yield tuples of n items at a time from iterable."""
    # batched is in the std library in python 3.12.
    if sys.version_info >= (3, 12):
        warnings.warn("batched is in the std library in python 3.12.", DeprecationWarning, stacklevel=2)

    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    # yield one tuple at a time until it's exhausted
    while batch := tuple(islice(it, n)):
        yield batch


def get_elt_file_assets(
    geo: Juri, datatype: GisData, stage_subdir: str | None, extension="*", expect_existing=False
) -> SimpleNamespace(files=list[Path], datatype=str, new_filename=Path | None):
    """Find filenames for this data type from filesystem. Filenames should be dates. Supports more than one
    matching data directory (eg zoning, zoning_height_bulk, and zoning_special), for which we prompt the user.
    Return filenames and metadata with latest date."""
    from elt.lib.extract.params import DATA_DIR

    # stage_dir = (DATA_DIR / geo.value / datatype.value / stage_dirname).resolve()
    stage_dir = (DATA_DIR / geo.value).resolve()

    # Find the data directory. If there are multiple, prompt the user to choose one.
    matching_data_dirs = list(chain(stage_dir.glob(f"{datatype.value}_*"), stage_dir.glob(datatype.value)))
    if len(matching_data_dirs) > 1:
        print("Choose which data dir to use:")
        for i, data_dir in enumerate(matching_data_dirs):
            print(f"{i+1}: {data_dir.name}")
        choice = int(Prompt.ask("Your choice? ", choices=[str(i + 1) for i in range(len(matching_data_dirs))]))
        stage_dir = matching_data_dirs[choice - 1]
    elif len(matching_data_dirs) == 1:
        stage_dir = matching_data_dirs[0]
    else:
        print(f"Error: no data directory found for {geo.value}/{datatype.value}")
        sys.exit(1)

    resolved_datatype = stage_dir.name  # eg "parcel", "zoning_height_bulk", ...
    # Append stage subdirectory (eg 0.shapefile) if specified
    stage_dir = stage_dir / stage_subdir if stage_subdir else stage_dir
    if not stage_dir.is_dir() and not expect_existing:
        # Confirm with the user that we should make the directory
        print(f"Directory {stage_dir} does not exist.")
        make_the_dir = Prompt.ask("Create it?", choices=["y", "n"])
        if make_the_dir == "y":
            stage_dir.mkdir(parents=True)
        assert stage_dir.is_dir()

    existing_files = sorted(stage_dir.glob(f"**/*.{extension}"), reverse=True) if stage_dir.is_dir() else []
    # files should be named YYMMDD[_more_stuff].extension
    dates_found = list({f.name[:6] for f in existing_files if f.name[:6].isdigit()})
    dates_found.sort(reverse=True)
    latest_files = [f for f in existing_files if f.name[:6] == dates_found[0]]
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    new_file = stage_dir / f"{now.strftime('%y%m%d')}.{extension}"
    if expect_existing:
        if not latest_files:
            print(f"Error: no matched files of extension {extension} found in {stage_dir}. ")
            print(f"\nYou should create a file like {new_file}")
            sys.exit(1)
        new_file = None
    data_date = date_parse(dates_found[0], yearfirst=True).date()
    return SimpleNamespace(
        latest_files=latest_files, resolved_datatype=resolved_datatype, data_date=data_date, new_filename=new_file
    )


def inspect_shapefile(shapefile_path):
    # Open the shapefile
    ds = DataSource(shapefile_path)

    # Access the layer (assuming there's only one layer in the shapefile)
    assert ds.layer_count == 1
    layer = ds[0]
    # Prepare a list to hold the data
    data = []
    headers = ["Geometry Type"] + layer.fields

    # Iterate through the first five features in the layer
    for feature in layer:
        # Get the geometry type (e.g., "Point", "Polygon", etc.)
        geometry_type = feature.geom.geom_type

        # Get the field values
        field_values = [feature.get(field) for field in layer.fields]

        # Append the geometry type and field values as a row in the data list
        data.append([geometry_type] + field_values)

    # Create a DataFrame using the data
    df = pd.DataFrame(data, columns=headers)

    # Print the DataFrame
    with pd.option_context("display.max_columns", None, "display.width", 150):
        for i in range(0, len(df), len(df) // 20):
            print(df.iloc[i : i + 5])
        # print(df)

    print("DONE inspecting")


def elt_model_with_custom_save(model_name_camel: str, save_fn: Callable) -> models.Model | None:
    """Return a version of the given ELT DB model which has a custom save method
    Args:
        model_name_camel (str): DB model name in CamelCase
        data_date (date): date to set in run_date field when saving
    Returns:
        models.Model: a Django model with a run_date field
    """
    try:
        raw_model = deepcopy(elt_models.__dict__[model_name_camel])
    except KeyError:
        return None

    def custom_save(self, *args, **kwargs):
        save_fn(self, *args, **kwargs)
        super(raw_model, self).save(*args, **kwargs)

    custom_save.__dict__["alters_data"] = True
    raw_model.save = custom_save
    return raw_model


def elt_model_with_run_date(
    model_name_camel: str,
    data_date: date,
) -> models.Model | None:
    """Return a version of the given ELT DB model which sets run-date as specified
    Args:
        model_name_camel (str): DB model name in CamelCase
        data_date (date): date to set in run_date field when saving
    Returns:
        models.Model: a Django model with a run_date field
    """
    return elt_model_with_custom_save(model_name_camel, lambda self: setattr(self, "run_date", data_date))


class H3LayerMapping(LayerMapping):
    """LayerMapping subclass which handles JSON fields."""

    def stats(self):
        print(f"DS name: {self.ds.name}")
        for layer in self.ds:
            print(f"Layer: {layer.name}")
            print(f"  Fields: {layer.fields}")
            print(f"  Geometry type: {layer.geom_type}")
            print(f"  Number of features (rows): {len(layer)}")
            # print(f"  SRS: {layer.srs}")

    def feature_kwargs(self, feature):
        """Override LayerMapping.feature_kwargs to handle JSON fields."""
        self.removed_mappings = dict({})
        json_kwargs = dict({})
        # process JSON fields locally
        json_fieldnames = [
            fieldname for fieldname in self.mapping if isinstance(self.model._meta.get_field(fieldname), JSONField)
        ]
        for json_fieldname in json_fieldnames:
            # pop the mapping for the JSON field so it doesn't get processed by the parent method
            self.removed_mappings[json_fieldname] = self.mapping.pop(json_fieldname)
            field = self.model._meta.get_field(json_fieldname)
            ogr_name = self.removed_mappings[json_fieldname]
            # Extract the values from the feature using the ogr_names in the list
            json_kwargs[json_fieldname] = {name: feature.get(name) for name in ogr_name}
        # call the parent method.
        kwargs = super().feature_kwargs(feature)
        # add in JSON field kwargs
        kwargs.update(json_kwargs)
        # Restore the mapping
        self.mapping.update(self.removed_mappings)

        return kwargs

    def verify_ogr_field(self, ogr_field, model_field):
        print("verify ogr field", ogr_field, model_field)
        return super().verify_ogr_field(ogr_field, model_field)

    def check_layer(self):
        """
        NILS: Copied from django's LayerMapping, edited to work with json fields.

        Check the Layer metadata and ensure that it's compatible with the
        mapping information and model. Unlike previous revisions, there is no
        need to increment through each feature in the Layer.
        """
        # The geometry field of the model is set here.
        # TODO: Support more than one geometry field / model.  However, this
        # depends on the GDAL Driver in use.
        self.geom_field = False
        self.fields = {}

        # Getting lists of the field names and the field types available in
        # the OGR Layer.
        ogr_fields = self.layer.fields
        ogr_field_types = self.layer.field_types

        # Function for determining if the OGR mapping field is in the Layer.
        def check_ogr_fld(ogr_map_fld):
            try:
                idx = ogr_fields.index(ogr_map_fld)
            except ValueError:
                raise LayerMapError('Given mapping OGR field "%s" not found in OGR Layer.' % ogr_map_fld)
            return idx

        # No need to increment through each feature in the model, simply check
        # the Layer metadata against what was given in the mapping dictionary.
        for field_name, ogr_name in self.mapping.items():
            # Ensuring that a corresponding field exists in the model
            # for the given field name in the mapping.
            try:
                model_field = self.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise LayerMapError('Given mapping field "%s" not in given Model fields.' % field_name)

            # Getting the string name for the Django field class (e.g., 'PointField').
            fld_name = model_field.__class__.__name__

            if isinstance(model_field, GeometryField):
                if self.geom_field:
                    raise LayerMapError("LayerMapping does not support more than one GeometryField per " "model.")

                # Getting the coordinate dimension of the geometry field.
                coord_dim = model_field.dim

                try:
                    if coord_dim == 3:
                        gtype = OGRGeomType(ogr_name + "25D")
                    else:
                        gtype = OGRGeomType(ogr_name)
                except GDALException:
                    raise LayerMapError('Invalid mapping for GeometryField "%s".' % field_name)

                # Making sure that the OGR Layer's Geometry is compatible.
                ltype = self.layer.geom_type
                if not (ltype.name.startswith(gtype.name) or self.make_multi(ltype, model_field)):
                    raise LayerMapError(
                        "Invalid mapping geometry; model has %s%s, "
                        "layer geometry type is %s." % (fld_name, "(dim=3)" if coord_dim == 3 else "", ltype)
                    )

                # Setting the `geom_field` attribute w/the name of the model field
                # that is a Geometry.  Also setting the coordinate dimension
                # attribute.
                self.geom_field = field_name
                self.coord_dim = coord_dim
                fields_val = model_field
            elif isinstance(model_field, models.ForeignKey):
                if isinstance(ogr_name, dict):
                    # Is every given related model mapping field in the Layer?
                    rel_model = model_field.remote_field.model
                    for rel_name, ogr_field in ogr_name.items():
                        idx = check_ogr_fld(ogr_field)
                        try:
                            rel_model._meta.get_field(rel_name)
                        except FieldDoesNotExist:
                            raise LayerMapError(
                                'ForeignKey mapping field "%s" not in %s fields.'
                                % (rel_name, rel_model.__class__.__name__)
                            )
                    fields_val = rel_model
                else:
                    raise TypeError("ForeignKey mapping must be of dictionary type.")
            else:
                # Nils: Skip JSONField check
                if model_field.__class__ is JSONField:
                    self.fields[field_name] = model_field
                    continue
                # Is the model field type supported by LayerMapping?
                if model_field.__class__ not in self.FIELD_TYPES:
                    raise LayerMapError('Django field type "%s" has no OGR mapping (yet).' % fld_name)

                # Is the OGR field in the Layer?
                idx = check_ogr_fld(ogr_name)
                ogr_field = ogr_field_types[idx]

                # Can the OGR field type be mapped to the Django field type?
                if not issubclass(ogr_field, self.FIELD_TYPES[model_field.__class__]):
                    raise LayerMapError(
                        'OGR field "%s" (of type %s) cannot be mapped to Django %s.'
                        % (ogr_field, ogr_field.__name__, fld_name)
                    )
                fields_val = model_field

            self.fields[field_name] = fields_val
