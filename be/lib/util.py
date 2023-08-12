from typing import NamedTuple


class LongLat(NamedTuple):
    long: float  # typically -125 to -115 (west)
    lat: float  # typically 35 to 40 (north)


def flatten_item(item, parent_key="", sep="_"):
    if isinstance(item, dict):
        return flatten_dict(item, parent_key=parent_key, sep=sep)
    elif isinstance(item, list):
        list_items = {}
        for i, v in enumerate(item):
            new_key = f"{parent_key}{sep}{i}"
            flattened_value = flatten_item(v, parent_key=new_key, sep=sep)
            if isinstance(flattened_value, dict):
                list_items.update(flattened_value)
            else:
                list_items[new_key] = flattened_value
        return list_items
    else:
        return item


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        flattened_value = flatten_item(v, parent_key=new_key, sep=sep)
        if isinstance(flattened_value, dict):
            items.extend(flattened_value.items())
        else:
            items.append((new_key, flattened_value))
    return dict(items)


def getattr_with_lookup_key(obj, attr, lookup_key=None):
    x = getattr(obj, attr)
    if lookup_key:
        return x[lookup_key]
    return x
