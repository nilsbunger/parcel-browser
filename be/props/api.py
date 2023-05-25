import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.errors import ValidationError
from ninja.security import django_auth
from pydantic import Extra

from facts.models import AddressFeatures, StdAddress
from lib.g_sheets import get_gsheet, get_rent_roll
from lib.ninja_api import ApiResponseSchema

from .models import PropertyProfile
from .schema import PropertyProfileOut

log = logging.getLogger(__name__)
props_api = NinjaAPI(auth=django_auth, csrf=True, urls_namespace="props", docs_decorator=staff_member_required)


class PermissiveSchema(Schema, extra=Extra.allow):
    pass


class PropertyCreateFormFieldsSchema(Schema):
    # formFields:
    streetAddress: str  # noqa: N815 - mixed case
    city: str
    zip: str


class CreatePropertySchema(Schema):
    formFields: PropertyCreateFormFieldsSchema  # noqa: N815 - mixed case
    features: AddressFeatures


class NewPropertyRespDataSchema(Schema):
    id: int


NewPropertyResponseSchema = ApiResponseSchema[NewPropertyRespDataSchema]


@props_api.exception_handler(ValidationError)
def custom_validation_errors(request, exc):
    # flush validation errors to console.
    print(exc.errors)
    return props_api.create_response(request, {"detail": exc.errors}, status=422)


@props_api.post("/profiles", response=NewPropertyResponseSchema, url_name="_create_property")
def _create_property(request, data: CreatePropertySchema):
    std_address, _created = StdAddress.objects.get_or_create(
        street_addr=data.formFields.streetAddress,
        city=data.formFields.city,
        zip=data.formFields.zip,
    )
    if _created:
        log.info(f"Created new property address id={std_address.id}")
        print("Created ", std_address.id)
    else:
        log.info(f"Found existing property address id={std_address.id}")

    std_address.address_features = data.features.dict()
    std_address.save()

    prop, _created = PropertyProfile.objects.get_or_create(legal_entity=None, address=std_address)
    if _created:
        log.info(f"Created new property profile id={prop.id}")
    else:
        log.info(f"Found existing property profile id={prop.id}")
    return NewPropertyResponseSchema(errors=False, message="Property created", data={"id": prop.id})


@props_api.get("/profiles/{prop_id}", response=PropertyProfileOut)
def _get_property(request, prop_id: int):
    # NOTE: this try/except block shouldn't be necessary but Pycharm debugger doesn't like an exception coming out of
    #  the view.
    try:
        prop = get_object_or_404(PropertyProfile, id=prop_id)
    except Http404:
        return props_api.create_response(request, {"errors": True, "message": "Not found"}, status=404)
    return prop


@props_api.get("/profiles", response=list[PropertyProfileOut], url_name="_list_properties")
def _list_properties(request):
    qs = PropertyProfile.objects.select_related("legal_entity", "address")
    log.info(f"Found {qs.count()} properties")
    log.info("")
    return list(qs)


# Verdant apt rent-roll and t12 google sheet
rent_roll_sheet_url = "https://docs.google.com/spreadsheets/d/1-ADiHnDJxAzCToVMd0aNeXRhdLniPja813ATcwNvJ_s/edit"
t12_sheet_url = "https://docs.google.com/spreadsheets/d/1KMXU0iDZPKJvcbEasme0bfMHVPsQ37NqtPohJ_DtbWo/edit"
rent_roll_gsheet = get_gsheet(rent_roll_sheet_url)


@props_api.get("/bov/{bov_id}", url_name="_get_bov")
def _get_bov(request, bov_id: int):
    rent_roll = get_rent_roll(rent_roll_gsheet)
    rent_roll_dict = rent_roll.to_dict(as_series=False)

    return {"errors": False, "message": "BOV retrieved", "data": rent_roll_dict}
