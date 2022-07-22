from typing import Union
from dataclasses import dataclass
from shapely.geometry import Polygon, MultiPolygon
from world.models import Parcel


@dataclass
class ParcelDC:
    geometry: MultiPolygon
    model: Parcel


# Helper type to define a MultiPolygon or Polygon
Polygonal = Union[Polygon, MultiPolygon]
