import logging
import urllib
from urllib.error import HTTPError, URLError

from django.http import Http404, HttpResponse
from django.template import engines
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from parsnip import settings

log = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class FrontEndProxyView(TemplateView):
    template_name = "react_layout.html"
