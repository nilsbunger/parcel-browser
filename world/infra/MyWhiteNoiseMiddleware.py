import logging

from django.contrib.staticfiles.storage import staticfiles_storage
from whitenoise.middleware import WhiteNoiseMiddleware
from whitenoise.string_utils import decode_if_byte_string

log = logging.getLogger(__name__)


class MyWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    # Override get_static_url to show errors
    def get_static_url(self, name):
        try:
            return decode_if_byte_string(staticfiles_storage.url(name))
        except ValueError:
            # log.exception("Whitenoise error in get_static_url")
            return None

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
