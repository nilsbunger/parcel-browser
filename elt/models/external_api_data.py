from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import blake2b
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
    lookup_key = models.CharField(max_length=512)
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

    def _fetch_json(self, url: str, params: dict[str, any], headers: dict[str, str]) -> dict[str, any]:
        query = urlencode(params, quote_via=quote)
        response = requests.get(url, query, headers=headers)
        response.raise_for_status()
        # if response.status_code != 200:
        #     raise Exception(f"API call to {url} returned an error: " + str(response.status_code))
        return response.json()

    def get(
        self,
        url: str,
        params: dict[str, any],
        lookup_key: str,
        hash_version: int,
        fetcher: Callable,
    ) -> ExternalApiData:
        # look in DB for data by
        # if not found, make request and save to DB
        lcl_key = "GET:" + lookup_key
        lookup_hash = int.from_bytes(blake2b(bytes(lcl_key, "utf-8"), digest_size=7).digest(), "little")
        cached_results = ExternalApiData.objects.filter(
            vendor=self.vendor, lookup_hash=lookup_hash, hash_version=hash_version
        )
        if len(cached_results) == 1:
            # cache hit
            print(f"CACHE HIT for {url} {params}")
            resp = cached_results[0]
            resp.cache_hit = True
            return resp
        elif len(cached_results) > 1:
            # TODO: instead of raising, compare to the lookup key to disambiguate
            raise Exception("Multiple results found for lookup hash")
        else:
            # cache miss -- fetch the data using requests.get(url, params)
            print(f"CACHE MISS... fetching data. LCL KEY={lcl_key}, HASH={hex(lookup_hash)}")
            json_resp = fetcher(url, params)
            # save to DB
            resp = ExternalApiData.objects.create(
                vendor=self.vendor,
                lookup_hash=lookup_hash,
                lookup_key=lcl_key,
                hash_version=hash_version,
                data=json_resp,
            )
            resp.cache_hit = False
            return resp


class ApiResponseStatus(BaseModel, extra=Extra.ignore):
    version: str
    code: int
    msg: str
    total: int
    page: int
    pagesize: int
