import logging
from pathlib import Path

from django.dispatch import receiver
from django.template.autoreload import get_template_directories
from django.utils.autoreload import file_changed
from parsnip.settings import DEV_ENV

log = logging.getLogger(__name__)


# In dev env, monitor django template changes and touch a frontend file to force a frontend rebuild.
# Without this, Parcel is unaware of django template changes, so it doesn't rebuild the frontend.
# This is a problem because we need tailwind to get rebuilt when a django template changes, to pick
# up any new tailwind classes used in a django template (which otherwise are not included by tailwind).
@receiver(file_changed, dispatch_uid="template_loaders_file_changed_2")
def _turboprop_template_changed(sender, file_path, **kwargs):
    assert DEV_ENV, "This should only be called in dev mode"
    if file_path.suffix != ".html":
        return
    for template_dir in get_template_directories():
        if template_dir in file_path.parents:
            # an HTML file in a template directory has changed. Force parcel to reload so we get new Tailwind classes.
            log.info("HTML file changed, touching tailwind.config.cjs to force parcel reload")
            Path("../fe/tailwind.config.cjs").touch()
            return True
