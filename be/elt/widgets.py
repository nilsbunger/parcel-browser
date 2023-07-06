import json
from builtins import super
from typing import Sequence

from django import forms
from django.utils.html import html_safe


@html_safe
class GlobalJsMediaPath:
    """Convert a JS module import into a global variable assignment for use in a django widget Media statement."""

    def __init__(self, url: str, objectNames: Sequence[str]):
        self.url = url
        self.objectNames = objectNames

    def __str__(self):
        # fmt:off
        return (
            '<script type="module">'
            + '\nimport { ' + ", ".join(self.objectNames) + ' } from "' + self.url + '";\n'
            + "\n".join([f"window.{name} = {name};" for name in self.objectNames])
            + "\n</script>"
        )
        # fmt:on


class JSONEditorWidget(forms.Widget):
    """Widget for editing JSON data in the admin. Uses "vanilla" version of
    https://github.com/josdejong/svelte-jsoneditor"""

    class Media:
        js = (
            GlobalJsMediaPath("https://unpkg.com/vanilla-jsoneditor/index.js", ["JSONEditor"]),
            # getattr(settings, "JSON_EDITOR_JS", 'dist/jsoneditor.min.js'),
            # "https://unpkg.com/vanilla-jsoneditor/index.js",
        )
        css = {
            "all": (
                # getattr(settings, "JSON_EDITOR_CSS", 'dist/jsoneditor.min.css'),
            )
        }

    template_name = "elt/django_json_widget.html"

    def __init__(self, attrs=None, mode="code", options=None, width=None, height=None):
        default_options = {
            "modes": ["text", "code", "tree", "form", "view"],
            "mode": mode,
            "search": True,
        }
        if options:
            default_options.update(options)

        self.options = default_options
        self.width = width
        self.height = height

        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["options"] = json.dumps(self.options)
        context["widget"]["width"] = self.width
        context["widget"]["height"] = self.height

        return context
