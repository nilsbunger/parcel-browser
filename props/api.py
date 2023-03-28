import logging
from typing import NamedTuple

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema
from ninja.security import django_auth
from pydantic import BaseModel, Extra

from facts.models import AddressFeatures, StdAddress
from .models import PropertyProfile
from .schema import PropertyProfileIn, PropertyProfileOut

log = logging.getLogger(__name__)
props_api = NinjaAPI(auth=django_auth, csrf=True, urls_namespace="props", docs_decorator=staff_member_required)


class PermissiveSchema(Schema, extra=Extra.allow):
    pass


class PropertyCreateFormFieldsSchema(Schema):
    # formFields:
    streetAddress: str
    city: str
    zip: str


class CreatePropertySchema(Schema):
    formFields: PropertyCreateFormFieldsSchema
    features: AddressFeatures


@props_api.post("/profiles")
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
    return {"id": prop.id}


@props_api.get("/profiles/{prop_id}", response=PropertyProfileOut)
def _get_property(request, prop_id: int):
    prop = get_object_or_404(PropertyProfile, id=prop_id)
    return prop


@props_api.get("/profiles", response=list[PropertyProfileOut])
def _list_properties(request):
    qs = PropertyProfile.objects.all()
    log.info(f"Found {qs.count()} properties")
    log.info("")
    return qs
