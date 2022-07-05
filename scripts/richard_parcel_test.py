"""
This file is used for testing different things about the parcel
"""

from notebooks.notebook_util import nb_exit, display_polys_on_lot
from lib.parcel_lib import *
import pandas as pd
from shapely.geometry import MultiPolygon
from world.models import Parcel, ZoningBase, BuildingOutlines
from shapely.ops import triangulate
from shapely.geometry import GeometryCollection
from django.core.serializers import serialize
import shapely
from shapely.ops import unary_union
import geopandas
import pprint
import json
import django
import os
import sys
import matplotlib.pyplot as plt


def run():
    # apn = '4302030800'  # working, original concave parcel
    # apn = '3090652100'  # interesting convex parcel
    # apn = '4301920200'  # Parcel with many adjacent parcels
    apn = '4360720700'  # Parcel with a back street
    # apn = '4255451500'  # parcel with lots of room, identified by Richard I think?

    # Get parcel and building info for this apn.
    parcel = get_parcel(apn)
    buildings = get_buildings(parcel)

    # convert building and parcel data into a UTM projection, which is a flat
    # geometry where each unit is 1 meter. This is stored as a GeoDataFrame
    parcel = models_to_utm_gdf([parcel])
    buildings = models_to_utm_gdf(buildings)

    street_edges, side_edges, back_edges = get_street_side_boundaries(parcel)
    to_visualize_edges = [side_edges.buffer(0.5),
                          back_edges.buffer(0.7),
                          street_edges.buffer(0.9)]

    # in the future, we store a list of the regions that we can't build on as a list.
    # This may include any buildings that we don't demolish, steep parts of the land,
    # other features such as pools etc, or setbacks.
    # Union all the geometries that we can't build to get it as a single Multipolygon
    cant_build = unary_union(buildings.geometry)

    # Calculate the available geometries
    avail_geom = get_avail_geoms(parcel.geometry[0], cant_build)

    # A lot data frame contains the building(s) and the parcel (the plot of land)
    lot_df = geopandas.GeoDataFrame(
        geometry=[cant_build, parcel.geometry[0].boundary], crs="EPSG:4326")

    # Display a graphic showing the building(s), and the available geometries we've calculated
    display_polys_on_lot(lot_df, [avail_geom, *to_visualize_edges])

    # Now find the largest rectangles we can fit on the available geometries
    placed_polys = find_largest_rectangles_on_avail_geom(
        avail_geom, num_rects=4, max_aspect_ratio=2.5)

    display_polys_on_lot(lot_df, [*placed_polys, *to_visualize_edges])
    plt.show()
