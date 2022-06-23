from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView


class MapView(TemplateView):
    template_name='map.html'