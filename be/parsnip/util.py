from dataclasses import dataclass
import re
import sys

from django.urls import NoReverseMatch, URLPattern, URLResolver
from math import floor, log10


# Print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def round_to_sig_figs(num: float, sig_figs: int):
    """Round a number to a specified number of significant figures"""
    return round(num, sig_figs - int(floor(log10(abs(num)))) - 1)


def keep_truthy(*args):
    """return a list of truthy values"""
    return [x for x in args if x]


def dict_keep_keys(dict, keys):
    """return a copy of dict with only keys kept"""
    return {k: dict[k] for k in keys if k in dict}


def dict_del_keys(dict, keys):
    """return a copy of dict with keys removed"""
    return {k: dict[k] for k in dict if k not in keys}


def dict_filter(dict, fn):
    """filter a dict's keys or values by a function (fn) that takes a tuple of (key, value)"""
    return {k: v for k, v in dict.items() if fn((k, v))}


def field_exists_on_model(model, field: str) -> bool:
    # A simple function to check if a field exists on a model
    try:
        # Check if this exists
        model._meta.get_field(field)
        return True
    except Exception:
        return False


placeholder_args = {"admin:app_list": ["world"]}


def each_url_with_placeholder(url_patterns, namespace=""):
    # Generator to iterate over the URL patterns in the resolver, returning each URL with placeholder args
    from django.urls import reverse

    # print (f"Called each_url_with_placeholder, ns={namespace}, url_patterns={url_patterns}")
    for url_pattern in url_patterns:
        # Get the URL pattern name and path
        if isinstance(url_pattern, URLResolver):
            # print (url_pattern.url_patterns)
            ns = namespace + (url_pattern.namespace + ":" if url_pattern.namespace else "")
            # print ("  Recursive call to each_url...")
            yield from each_url_with_placeholder(url_pattern.url_patterns, ns)
        else:
            assert isinstance(url_pattern, URLPattern)
            if url_pattern.name:
                viewname = namespace + url_pattern.name
            elif "view_initkwargs" in url_pattern.callback.__dict__:
                viewname = url_pattern.callback.view_initkwargs["pattern_name"]
            else:
                viewname = url_pattern.callback
            args = placeholder_args.get(viewname, range(1, url_pattern.pattern.regex.groups + 1))
            try:
                url = reverse(viewname, args=args)
            except NoReverseMatch:
                print(f"Can't test {viewname}")
                continue
            # if not url_pattern.name:
            #     url = reverse(url_pattern.callback.view_initkwargs['pattern_name'], args=args)
            #     print ("UH OH")
            #     ...
            # else:
            #     url = reverse(namespace + url_pattern.name, args=args)
            yield url


@dataclass
class RegexEqual(str):
    """Regex matching for"match / case. Example at https://martinheinz.dev/blog/78"""

    string: str
    match: re.Match = None

    def __eq__(self, pattern):
        self.match = re.search(pattern, self.string)
        return self.match is not None

    def __getitem__(self, group):
        return self.match[group]
