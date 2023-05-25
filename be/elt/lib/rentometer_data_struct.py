from __future__ import annotations

from pydantic import BaseModel, Extra

extra_setting = Extra.forbid


class Link(BaseModel):
    rel: str
    href: str


class RentometerResponse(BaseModel, extra=extra_setting):
    address: str | None
    latitude: float
    longitude: float
    bedrooms: int
    baths: str
    building_type: str
    look_back_days: int
    mean: int
    median: int
    min: int
    max: int
    percentile_25: int
    percentile_75: int
    std_dev: int
    samples: int
    radius_miles: float
    quickview_url: str
    credits_remaining: int
    token: str
    links: list[Link]
