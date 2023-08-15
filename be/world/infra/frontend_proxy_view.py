import logging
import subprocess

from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from django.conf import settings

log = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class FrontEndProdProxyView(TemplateView):
    template_name = "react_layout.html"


class FrontEndLocalProxyView(TemplateView):
    template_name = "react_layout.html"

    def yarn_dev_running(self):
        """Check if yarn dev is running on the system."""
        try:
            result = subprocess.check_output(["pgrep", "-f", "yarn dev"], stderr=subprocess.STDOUT).decode("utf-8")
            return True if result else False
        except subprocess.CalledProcessError:
            return False

    def render_to_response(self, context, **response_kwargs):
        if not self.yarn_dev_running():
            # If yarn dev isn't running, return simple HTML string
            return HttpResponse(
                """
            <div style="background-color: red; color: white; padding: 10px;">
                Please start yarn dev on your machine!
            </div>
            """
            )

        # Otherwise, continue with the usual rendering
        return super().render_to_response(context, **response_kwargs)


FrontEndProxyView = FrontEndLocalProxyView if settings.DEV_ENV else FrontEndProdProxyView
