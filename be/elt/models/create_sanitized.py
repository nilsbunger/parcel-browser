from copy import deepcopy

from elt.lib.excel.extract_from_excel import camelcase


class CreateSanitizedMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "choice_fields") or not hasattr(cls, "str_fields"):
            cls.choice_fields = [f for f in cls._meta.fields if f.choices]
            cls.str_fields = [f for f in cls._meta.fields if f.get_internal_type() == "CharField"]
        return super().__new__(cls)

    @classmethod
    def create_sanitized(cls, *args, **kwargs):
        """Create an instance of this model, with enums mapped from values and string fields limited to 250 characters"""
        obj = cls()
        init_vals = deepcopy(kwargs)
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
