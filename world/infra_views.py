import urllib
from urllib.error import HTTPError

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
# In dev, this requires running a frontend server at localhost:1234 in dev by executing `yarn dev` in the frontend/ directory.

# TODO: prod version hasn't been set up
frontend_proxy_prod_view = TemplateView.as_view(template_name='index.html')


def frontend_proxy_dev_view(request, path, upstream='http://localhost:1234'):
    upstream_url = upstream + '/' + path

    try:
        response = urllib.request.urlopen(upstream_url)
    except HTTPError as e:
        if e.code == 404:
            raise Http404
        else:
            raise e

    content_type = response.headers.get('Content-Type')
    if content_type == 'text/html; charset=UTF-8':
        # run HTML through the template engine
        response_text = response.read().decode()
        content = engines['django'].from_string(response_text).render()
    else:
        content = response.read()
    return HttpResponse(
        content,
        content_type=content_type,
        status=response.status,
        reason=response.reason,
    )


frontend_proxy_view = frontend_proxy_dev_view if settings.DEBUG else frontend_proxy_prod_view
