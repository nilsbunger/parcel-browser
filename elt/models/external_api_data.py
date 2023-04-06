from abc import ABC
from dataclasses import dataclass
from typing import TypeVar
from urllib.parse import quote, urlencode

import requests
from django.contrib.gis.db import models
from pydantic import BaseModel, Extra


class ExternalApiData(models.Model):
    class Vendor(models.IntegerChoices):
        ATTOM = 1
        SOMEONE_ELSE = 99

    vendor = models.IntegerField(choices=Vendor.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField()
    lookup_hash = models.BigIntegerField()
    lookup_key = models.CharField(max_length=64)
    hash_version = models.IntegerField(
        default=1
    )  # hash and data version - increase when using a new hash function or changing the data

    class Meta:
        indexes = [
            models.Index(fields=["vendor", "lookup_hash", "hash_version"]),
        ]


T = TypeVar("T")


@dataclass(kw_only=True)
class CacheableApi(ABC):
    vendor: ExternalApiData.Vendor

    def get(
        self,
        url: str,
        params: dict[str, any],
        headers: dict[str, str],
        lookup_key: str,
        hash_version: int,
        paged: bool,
    ) -> ExternalApiData:
        # look in DB for data by
        # if not found, make request and save to DB
        lookup_hash = hash("GET:" + lookup_key)
        cached_results = ExternalApiData.objects.filter(
            vendor=self.vendor, lookup_hash=lookup_hash, hash_version=hash_version
        )
        if len(cached_results) == 0:
            # fetch the data using requests.get(url, params)
            if paged:
                params["page"] = 1
                params["pagesize"] = 200
            query = urlencode(params, quote_via=quote)
            print(query)
            response = requests.get(url, query, headers=headers)
            if response.status_code != 200:
                raise Exception(f"API call to {url} returned an error: " + str(response.status_code))
            json_resp = response.json()
            status = ApiResponseStatus.parse_obj(json_resp["status"])
            if status.msg != "SuccessWithResult":
                print(f"API call to {url} returned an error: " + status.msg)
            if paged and status.pagesize <= status.total:
                raise NotImplementedError("Paged API calls not implemented yet")

            # save to DB
            resp = ExternalApiData.objects.create(
                vendor=self.vendor,
                lookup_hash=lookup_hash,
                lookup_key=lookup_key,
                hash_version=hash_version,
                data=json_resp,
            )
            resp.cache_hit = False
            return resp
        elif len(cached_results) == 1:
            resp = cached_results[0]
            resp.cache_hit = True
            return resp
        else:
            # TODO: instead of raising, compare to the lookup key to disambiguate
            raise Exception("Multiple results found for lookup hash")


class ApiResponseStatus(BaseModel, extra=Extra.ignore):
    version: str
    code: int
    msg: str
    total: int
    page: int
    pagesize: int
