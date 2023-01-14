import urllib
from urllib.error import HTTPError, URLError

from django.http import Http404, HttpResponse
from django.template import engines
from django.views.generic import TemplateView

from mygeo import settings


# ------------------------------------------------------
# Proxy URL calls to frontend/ to the frontend server
# ------------------------------------------------------

# Proxy requests to JS front-end files that are served separately. This is needed to create a modern JS pipeline in
# Django. We're using the "hybrid app" method as described in
# https://fractalideas.com/blog/making-react-and-django-play-well-together-hybrid-app-model/
# In dev, this requires running a frontend server at localhost:1234 in dev by executing `yarn dev` in
# the frontend/ directory.


class FrontEndProxyView(TemplateView):
    pass


# PRODUCTION SERVING: We just serve index.html for views we handle, then the react-router handles the rest.
frontend_proxy_prod_view = FrontEndProxyView.as_view(template_name="index.html")


# DEVELOPMENT SERVING: Proxy requests to frontend server


def frontend_proxy_dev_view(request, path, upstream="http://localhost:1234"):
    full_path = request.get_full_path()  # includes query string
    upstream_url = upstream + full_path
    try:
        response = urllib.request.urlopen(upstream_url)
        print("Proxying to", upstream_url)
        headers = {}
        if "Accept" in request.headers:
            headers["Accept"] = request.headers["Accept"]
        req = urllib.request.Request(upstream_url, headers=headers, data=request.body, method=request.method)
        response = urllib.request.urlopen(req)
    except HTTPError as e:
        if e.code == 404:
            print(f"Got 404 from upstream... url={upstream_url}")
            raise Http404
        elif e.code == 500:
            return HttpResponse("Frontend Server Error", status=500)
        else:
            raise e
    except URLError as e:
        if type(e.reason) == ConnectionRefusedError:
            # Frontend is probably not running
            return HttpResponse("Can't connect to frontend... Do you need to start yarn dev?")

    content_type = response.headers.get("Content-Type")
    if content_type == "text/html; charset=UTF-8":
        # run HTML through the template engine
        response_text = response.read().decode()
        content = engines["django"].from_string(response_text).render()
    else:
        content = response.read()
    return HttpResponse(
        content,
        content_type=content_type,
        status=response.status,
        reason=response.reason,
    )


frontend_proxy_view = frontend_proxy_dev_view if settings.DEBUG or settings.TEST_ENV else frontend_proxy_prod_view
