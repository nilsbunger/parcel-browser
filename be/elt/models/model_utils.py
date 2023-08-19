import pandas as pd
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from elt.lib.extract.excel import camelcase

# String representation of model types
raw_str = {
    "RawSfHeTableA": ("HE A {}: {}", "mapblklot", "address"),
    "RawSfHeTableB": ("HE B {}: {} ", "mapblklot", "address"),
    "RawSfHeTableC": ("HE C {}: {}", "zoning", "zoning_name"),
    "RawSfParcel": ("Parcel {}: {}", "blklot", "resolved_address"),
    "RawSfParcelWrap": ("Wrap {} he_a={}, he_b={}", "parcel", "he_table_a", "he_table_b"),
    "RawCaliResourceLevel": ("Resource {}: {}, {}", "fips", "cnty_nm", "oppcat"),
    "RawReportall": ("Reportall {}: {}", "parcel_id", "situs"),
    "RawSfRentboardHousingInv": (
        "Rentboard {}: {}, {} : ${}",
        "parcel_number",
        "unit_address",
        "unit_number",
        "monthly_rent",
    ),
}


class SanitizedRawModelMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_field_display_value(self, fieldname):
        display_fn = getattr(self, f"get_{fieldname}_display", None)
        if display_fn:
            return display_fn()
        return getattr(self, fieldname)

    def _get_FIELD_display(self, field):  # noqa:N802
        field_text = super()._get_FIELD_display(field)
        # if field_text[0] == "A" and field_text[1].isdigit():
        #     field_text = field_text[1:]
        # field_text = field_text.replace(" ", "_")
        return field_text

    def __str__(self) -> str:
        """Return a string representation of the model instance. Fill in fields that are fetched already"""
        clsname = self.__class__.__name__
        format_entry = raw_str.get(clsname)
        if not format_entry:
            return super().__str__()
        values = []
        for fieldname in format_entry[1:]:
            if fieldname in self.__dict__:  # the field has been fetched
                values.append(self._get_field_display_value(fieldname))
            else:
                values.append(f"<{fieldname} not fetched>")
        return f"{format_entry[0].format(*values)}"

    def __new__(cls, *args, **kwargs):
        """Patch object creation to have a list of fields to sanitize"""
        if not hasattr(cls, "choice_fields") or not hasattr(cls, "str_fields"):
            cls.choice_fields = [f for f in cls._meta.fields if f.choices]
            cls.str_fields = [f for f in cls._meta.fields if f.get_internal_type() == "CharField"]
        return super().__new__(cls)

    @classmethod
    def create_sanitized(cls, row, df, *args, **kwargs):
        """Create an instance of this model with enums mapped from values & string fields limited to 250 characters"""

        obj = cls()
        init_vals = dict(row)
        # get rid of NaNs (float), NAs (int) and NaTs (timestamps) in all fields.
        # This could probably be done more efficiently once for the DF.
        for key in init_vals:
            if pd.isnull(init_vals[key]):
                init_vals[key] = None
            # if type(init_vals[key]) == float and isnan(init_vals[key]):
            #     init_vals[key] = None
            # if df.dtypes[key].type is np.int64 and pd.isna(init_vals[key]):
            #     init_vals[key] = None
            # if is_datetime64_any_dtype(df.dtypes[key])

        init_vals["run_date"] = kwargs["run_date"]
        for field in cls.choice_fields:
            str_val = camelcase(init_vals[field.name])
            if str_val is None:
                init_vals[field.name] = None
            else:
                # lowercase for enum comparisons b/c Django messes with enum casing
                str_val = str_val.lower()
                enum_val = next(
                    (choice for choice in field.choices if choice[1].lower().replace(" ", "_") == str_val), None
                )
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

    def get_admin_url(self):
        """Return the admin URL. Used by admin inlines."""
        return reverse(f"admin:{self._meta.app_label}_{self._meta.model_name}_change", args=[self.pk])

    @classmethod
    def histo(cls, *, qs=None, field: str) -> QuerySet:
        """Return a queryset with a count of each value of FIELD within a queryset"""
        if not qs:
            qs = cls.objects.all()
        return qs.values(field).annotate(count=models.Count(field)).order_by("count")
