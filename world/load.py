

# currently you run this with ./manage.py shell, then `from world import load` then `load.run()`
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import WorldBorder, parcel_mapping, world_mapping, Parcel

# shpfile = Path(__file__).resolve().parent / 'data' / 'TM_WORLD_BORDERS-0.3.shp'
shpfile = Path(__file__).resolve().parent / 'data' / 'PARCELS.shp'

def run(verbose=False):
    # lm = LayerMapping(WorldBorder, shpfile, world_mapping, transform=False)
    lm = LayerMapping(Parcel, shpfile, parcel_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
