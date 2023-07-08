import copy
from dataclasses import dataclass, field
from datetime import date
from functools import reduce
from math import isnan
import re
import sys
from typing import Callable

from charset_normalizer.cli.normalizer import query_yes_no
from dateutil.parser import parse as date_parse
from django.db import models
from pandas import DataFrame, ExcelFile
import pandas as pd

from elt.lib.elt_utils import batched, elt_model_with_run_date, get_elt_pipe_filenames, pipestage_prompt
from elt.lib.types import GisData, Juri
from parsnip.settings import BASE_DIR

MODELS_DIR = BASE_DIR / "elt" / "models"


def default_field(obj):
    return field(default_factory=lambda: copy.deepcopy(obj))


@dataclass(frozen=True)
class ExcelParseArgs:
    enum_cols: list[str] = default_field([])
    int_cols: list[str] = default_field([])
    skip_cols: list[str] = default_field([])
    fn_cols: dict[str, Callable] = default_field([])
    header_rows: list[int] = None


def sanitize(name):
    """Return a name converted to lowercase and underscored, with non-alphanumeric characters removed."""
    # # Fetch everything up to first non-alpha character, while also having tighter rules for first character.
    if (name is None) or (type(name) == float and isnan(name)):
        return None
    if str(name) == "nan":
        print("unexpected nan")
        raise ValueError("Unexpected nan - should be turned into None")
    # remove non-alphanumeric characters, replacing them with an underscore
    base = re.sub("[^A-Za-z0-9_\- ]", "_", str(name).strip())
    # add an underscore in front of each capitalized word
    base = re.sub("([^A-Z])([A-Z])", r"\1_\2", base)
    # lowercase the result and convert multiple spaces, dashes, and underscores to an underscore
    base = re.sub("[ _\-]+", "_", base.lower())
    base = base.strip("_")  # remove leading or trailing underscore
    if base[0].isdigit():
        # first character is a digit - prepend an "A". Can't use underscore b/c Django converts it to spaces.
        base = "A" + base
    return base


def confirm_overwrite(fname):
    if (fname).exists():
        print(f"WARNING: {fname}' already exists...")
        if not query_yes_no("Overwrite?", default="no"):
            print("Skipping...")
            return False
    return True


def camelcase(name):
    """Return a ready-for-DB camel-cased name based on an arbitrary incoming name."""
    m = sanitize(name)
    if m is None:
        return None
    base_str = m.strip().capitalize()
    # capitalize each word... but if we see a sequence of numbers, keep the underscores.
    try:
        base_str = reduce(
            lambda s, t: s + (t.capitalize()) if t[0].isalpha() or s[-1].isalpha() else s + "_" + t,
            re.split("[ _]", base_str),
        )
    except Exception as e:
        print(f"Error processing {name}: {e}")
        raise e
    base_str = base_str
    return base_str


pandas_field_to_db_field = {
    "object": "models.CharField(max_length=254, null=True, blank=True)",
    "int64": "models.IntegerField(null=True, blank=True)",
    "Int64": "models.IntegerField(null=True, blank=True)",  # Int64 allows nulls, while int64 doesn't.
    "float64": "models.FloatField(null=True, blank=True)",
    "bool": "models.BooleanField(null=True, blank=True)",
    "datetime64[ns]": "models.DateField(null=True, blank=True)",
}


def parse_excel(*, xls, full_sheet_name, friendly_sheet_name, parse_args: ExcelParseArgs):
    """Parse excel file into a dataframe with processing like enum mapping and datatype munging."""
    df = pd.read_excel(xls, full_sheet_name, header=parse_args.header_rows)
    orig_cols = list(df.columns)  # keep a copy of the original column names so we can compare
    # Sanitize column names
    df.rename(columns=lambda x: sanitize(x), inplace=True)

    cols = list(df.columns)

    cols_to_check = parse_args.enum_cols + parse_args.skip_cols + parse_args.int_cols
    for col in cols_to_check:
        if col not in cols:
            raise ValueError(f"Error: column {col} not found in sheet {friendly_sheet_name}. Columns are {cols}")
    # convert columns to appropriate type
    try:
        df.drop(columns=parse_args.skip_cols, inplace=True)
        col: str
        for col in parse_args.fn_cols:
            df[col] = df[col].map(parse_args.fn_cols[col])  # map applies a function to a column
        for col in parse_args.enum_cols:
            df[col] = df[col].astype("category")
        for col in parse_args.int_cols:
            df[col] = df[col].astype("Int64")  # Int64 allows for nulls
    except Exception as e:
        print(f"Error processing sheet {friendly_sheet_name}: {e}")
        raise e
    print("df:", df)
    print("df datatypes:", [(x, df[x].dtype.name) for x in df.columns])
    category_cols = [
        df[col_name]
        for col_name in df.columns
        if getattr(df[col_name].dtype, "is_dtype", lambda x: False)("category")
    ]
    print("\nColumn names and types:")
    print(df.dtypes)
    print("\nCategory columns:")
    for col in category_cols:
        print(f"Column {col.name}: {len(col.cat.categories)} columns")
        if len(col.cat.categories) < 20:
            print(list(col.cat.categories))
        else:
            print("Too many categories to list")

    return df


def parse_sf_he(xls: ExcelFile, full_sheet_name: str, friendly_sheet_name: str):
    """Parse the SF HE data from excel. Called by extract_from_excel dynamically."""
    match friendly_sheet_name:
        case "table_a":
            # fmt:off
            parse_args = ExcelParseArgs(
                enum_cols=[
                    "ex_gp_des", "ex_zoning", "ex_use_vac", "infra", "public", "site_stat", "id_last2", "opt1"
                ],
                int_cols=["zip5"],
                skip_cols=["jurisdict"],
                # remove dashes from parcel APN field
                fn_cols=dict({"mapblklot": lambda x: x.replace("-", "") if type(x) == str else x}),
                header_rows=[1],
            )
            # fmt:on
        case "table_b":
            # fmt:off
            parse_args = ExcelParseArgs(
                enum_cols=['shortfall', 'ex_gp_type', 'ex_zoning', 'm1_gp_type', 'm2_gp_type', 'm3_gp_type',
                           'm1_zoning', 'm2_zoning', 'm3_zoning', 'vacant', 'ex_use', 'infra'],
                int_cols=["zip5"],
                skip_cols=["jurisdict"],
                # remove dashes from parcel APN field
                fn_cols=dict({"mapblklot": lambda x: x.replace("-", "") if type(x) == str else x}),
                header_rows=[1],
            )
            # fmt:on
        case "table_c":
            parse_args = ExcelParseArgs(enum_cols=["zoning_type"], header_rows=[2])
        case _:
            print(f"Unprocessed sheet: {full_sheet_name}")
            return None
    print(f"Processing Sheet {full_sheet_name} (aka {friendly_sheet_name})...")
    df = parse_excel(
        xls=xls, full_sheet_name=full_sheet_name, friendly_sheet_name=friendly_sheet_name, parse_args=parse_args
    )
    return df


def parse_sf_rentboard(xls: ExcelFile, full_sheet_name: str, friendly_sheet_name: str):
    def parse_year(x):
        if x == "Year unknown (no information available)":
            return 0
        elif x == "Year Unknown (more than 20 years)":
            return 1
        elif x == "Year Unknown (within past 10-20 years)":
            return 2
        elif x == "Year Unknown (within past 5-10 years)":
            return 3
        elif x == "Year Unknown (within past five years)":
            return 4
        elif isnan(x):
            return None
        try:
            int(x)
            return x
        except ValueError:
            print(f"something that won't parse as int in an int column:{x}")
            return x

    args = ExcelParseArgs(
        # fmt:off
        enum_cols=[
            "case_type_name", "occupancy_type", "bedroom_count", "bathroom_count", "square_footage", "monthly_rent",
            "base_rentinclude_utility", "month", "past_occupancy", "contact_association", "contact_type",
        ],
        # fmt:on
        int_cols=["day", "year"],
        skip_cols=["occupancy_date", "signature"],
        fn_cols={
            "bedroom_count": lambda x: "FivePlus" if x == "5+" else x,
            "parcel_number": lambda x: x.replace("-", "") if type(x) == str else x,
            "day": lambda x: None if x == "Day unknown" else x,
            "year": parse_year,
        },
        header_rows=[0],
    )

    df = parse_excel(
        xls=xls, full_sheet_name=full_sheet_name, friendly_sheet_name=friendly_sheet_name, parse_args=args
    )
    return df


def camel_to_verbose(name: str):
    """Convert a camelcase name to a string with spaces between words, maintaining capitalization."""
    return re.sub(r"([A-Z])", r" \1", name).strip()


def generate_py_for_model(model_name_camel: str, sheet_df: DataFrame) -> str:
    """Create python code for a django model based on the columns in the sheet_df."""
    header_lines = [
        "# Autogenerated by extract_from_excel.py",
        "from django.contrib.gis.db import models",
        "from elt.models.model_utils import SanitizedModelMixin",
        "",
        f"class {model_name_camel}(SanitizedModelMixin, models.Model):",
        f"    class Meta:",
        f'        verbose_name = "{camel_to_verbose(model_name_camel)} [Excel]"',
        f'        verbose_name_plural = "{camel_to_verbose(model_name_camel)} [Excel]"',
    ]
    # main body lines
    lines = [f"    run_date = models.DateField()"]
    # lines for enums (need to come before usage)
    enum_lines = []
    for col in sheet_df.columns:
        dt = sheet_df[col].dtype
        if dt.name in pandas_field_to_db_field:
            lines.append(f"    {col} = {pandas_field_to_db_field[dt.name]}")
        elif dt.name == "category":
            # create text for a django enum in the model class
            # get the enum values from the pandas column
            enum_name = camelcase(f"{col}_enum")
            used_cats = set({})
            lines.append(f"    {col} = models.IntegerField(choices={enum_name}.choices, null=True, blank=True)")
            enum_lines.append(f"\n    class {enum_name}(models.IntegerChoices):")
            cat_mappings = dict({})
            for idx, cat in enumerate(sheet_df[col].cat.categories):
                safe_cat = sanitize(cat).upper()
                cat_mappings[safe_cat] = cat
                if safe_cat in used_cats:
                    print(f"WARNING: Skipping duplicate category: {cat}.(prev name={cat_mappings[safe_cat]}")
                else:
                    used_cats.add(safe_cat)
                    enum_lines.append(f"        {safe_cat} = {idx}")
        else:
            raise ValueError(f"ERROR: Unhandled data type: {dt}")
    lines = header_lines + enum_lines + [""] + lines
    result = "\n".join(lines)
    return result + "\n"


def write_db_model_file(model_name, model_name_camel, sheet_df):
    generated_python = generate_py_for_model(model_name_camel, sheet_df)
    if confirm_overwrite(MODELS_DIR / f"{model_name}.py"):
        print("Writing to ", MODELS_DIR / f"{model_name}.py")
        with open(MODELS_DIR / f"{model_name}.py", "w") as f:
            f.write(generated_python)


def save_df_to_db(sheet_df: DataFrame, db_model: models.Model, run_date: date):
    """Save a dataframe to a django model"""
    db_model_with_date: models.Model | None = elt_model_with_run_date(db_model.__name__, run_date)
    assert db_model_with_date
    df_records = sheet_df.to_dict("records")
    batch_size = 10
    print(f"Saving {len(df_records)} records to {db_model_with_date.__name__} ({batch_size} at a time)...")
    for batch in batched(sheet_df.iterrows(), batch_size):
        print(".", end="")
        # noinspection PyCallingNonCallable
        models = [db_model_with_date.create_sanitized(row, sheet_df, run_date=run_date) for idx, row in batch]
        try:
            db_model_with_date.objects.bulk_create(models)
        except Exception as e:
            print(e)
            print("raising")
            raise e

    print("\nDONE SAVING")


def extract_from_excel(geo: Juri, datatype: GisData, thru_data=None):
    """ """
    print(f"Extract from excel: geo={geo.value}, data={datatype.value}")
    pipestage_dirname = "0.excel"
    existing_files, resolved_datatype, _ = get_elt_pipe_filenames(
        geo, datatype, pipestage_dirname, extension="xlsx", expect_existing=True
    )
    latest_file = existing_files[0]
    print("Extracting from latest matching file: ", latest_file)
    date_from_filename = date_parse(latest_file.stem.split("_")[0], yearfirst=True).date()

    # load the excel file from latest_file
    xls = pd.ExcelFile(latest_file)
    full_sheet_names = xls.sheet_names
    full_sheet_names.reverse()
    for full_sheet_name in full_sheet_names:
        sanitized_sheet_name = sanitize(re.match("^[^\-]+", full_sheet_name)[0])
        parser_fn = globals()[f"parse_{geo.name}_{resolved_datatype}"]
        model_name = "raw_" + geo.name + "_" + resolved_datatype + "_" + sanitized_sheet_name
        model_name_camel = camelcase(model_name)

        # Call parser for sheet (eg: parse_sf_he)
        sheet_df: DataFrame | None = parser_fn(xls, full_sheet_name, sanitized_sheet_name)
        if sheet_df is None:
            continue  # skip unparsed sheets
        # Get DB model if it exists
        db_model = elt_model_with_run_date(model_name_camel, date_from_filename)
        # if model doesn't exist, generate python for the model and write the file.
        if not db_model:
            print(f"DB model {model_name_camel} doesn't exist. Generating python code for it...")
            write_db_model_file(model_name, model_name_camel, sheet_df)
        else:
            cnt = db_model.objects.filter(run_date=date_from_filename).count()
            # confirm to overwrite or extend existing data with same run_date
            intent = pipestage_prompt(is_incremental=True, num_existing_entries=cnt, run_date=date_from_filename)
            if cnt > 0 and intent == "c":
                db_model.objects.filter(run_date=date_from_filename).delete()
            if intent in ["c", "i"]:
                # create or incrementally update
                save_df_to_db(sheet_df, db_model, run_date=date_from_filename)

    print("Done")
