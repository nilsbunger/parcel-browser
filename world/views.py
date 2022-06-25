import urllib
from urllib.error import HTTPError

from django.core.serializers import serialize
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.template import engines

# Create your views here.
from world.models import Parcel, BuildingOutlines


class MapView(LoginRequiredMixin, TemplateView):
    template_name='map.html'


class ParcelView(LoginRequiredMixin, View):
    template_name = 'parcel-detail.html'

    def get(self, request, apn, *args, **kwargs):
        return render(request, self.template_name, {})

class ParcelData(LoginRequiredMixin, View):
    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        print (parcel)

        buildings = BuildingOutlines.objects.filter(geom__contains=parcel.geom)
        print (buildings)
        serialized = serialize('geojson', [parcel], geometry_field='geom', fields=('apn', 'geom', ))
        return HttpResponse(serialized, content_type='application/json')


# hybrid app as per https://fractalideas.com/blog/making-react-and-django-play-well-together-hybrid-app-model/
def catchall_dev(request, path, upstream='http://localhost:1234'):
    upstream_url = upstream + '/' + path

    try:
        response = urllib.request.urlopen(upstream_url)
    except HTTPError as e:
        if e.code == 404:
            raise Http404
        else: raise e

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

catchall_prod = TemplateView.as_view(template_name='index.html')

catchall = catchall_dev if settings.DEBUG else catchall_prod