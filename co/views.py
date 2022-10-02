from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


# Create your views here.


class CoParcelDetail(LoginRequiredMixin, View):
    template_name = "co-parcel-detail.html"

    def get(self, request, apn, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {
                # "parcel_data": serialized_parcel,
                # "building_data": serialized_buildings,
                # "latlong": str(list(parcel_data_frame.centroid[0].coords)[0]),
                # "lot_size": lot_square_feet,
            },
        )
