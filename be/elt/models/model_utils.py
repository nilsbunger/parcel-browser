from copy import deepcopy
from math import isnan

from elt.lib.excel.extract_from_excel import camel_to_verbose, camelcase


# String representation of model types
raw_str = {
    "RawSfHeTableA": ("APN={}, {}", "mapblklot", "address"),
    "RawSfHeTableB": ("APN={}, {} ", "mapblklot", "address"),
    "RawSfHeTableC": ("{}: {}", "zoning", "zoning_name"),
    "RawSfParcel": ("APN={}. {}", "blklot", "resolved_address"),
    "RawSfParcelWrap": ("Wrap {} he_a={}, he_b={}", "parcel", "he_table_a", "he_table_b"),
    "RawCaliResourceLevel": ("{}: {}, {}", "fips", "cnty_nm", "oppcat"),
    "RawSfReportall": ("{}: {}", "parcel_id", "situs"),
}


class SanitizedModelMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        """Return a string representation of the model instance for admin"""
        clsname = self.__class__.__name__
        format_entry = raw_str.get(clsname)
        if not format_entry:
            return super().__str__()
        values = [getattr(self, fieldname) for fieldname in format_entry[1:]]
        return f"{format_entry[0].format(*values)}"

    def __new__(cls, *args, **kwargs):
        """Patch object creation to have a list of fields to sanitize"""
        if not hasattr(cls, "choice_fields") or not hasattr(cls, "str_fields"):
            cls.choice_fields = [f for f in cls._meta.fields if f.choices]
            cls.str_fields = [f for f in cls._meta.fields if f.get_internal_type() == "CharField"]
        return super().__new__(cls)

    @classmethod
    def create_sanitized(cls, *args, **kwargs):
        """Create an instance of this model with enums mapped from values & string fields limited to 250 characters"""

        obj = cls()
        init_vals = deepcopy(kwargs)
        # get rid of NaNs in all fields
        for key in init_vals:
            if type(init_vals[key]) == float and isnan(init_vals[key]):
                init_vals[key] = None
        for field in cls.choice_fields:
            str_val = camelcase(init_vals[field.name])
            if str_val is None:
                init_vals[field.name] = None
            else:
                # lowercase for enum comparisons b/c Django messes with enum casing
                str_val = str_val.lower()
                enum_val = next((choice for choice in field.choices if choice[1].lower() == str_val), None)
                if not enum_val:
                    raise ValueError(f"Could not find enum value for {field.name}={str_val}")
                init_vals[field.name] = enum_val[0]
        # limit field length of string fields to 250 characters
        for field in cls.str_fields:
            try:
                if type(init_vals[field.name]) == str:
                    init_vals[field.name] = init_vals[field.name][:250]
            except Exception as e:
                print(e)
                print(init_vals[field.name])
                raise e
        # set fields of obj to values from init_vals
        for field in init_vals:
            setattr(obj, field, init_vals[field])
        return obj
