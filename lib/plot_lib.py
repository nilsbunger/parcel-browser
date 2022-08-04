# Helper functions to plot geographical data

import pyproj
from lib.types import ParcelDC
import matplotlib.pyplot as plt
from lib.parcel_lib import *
import geopandas
import matplotlib
# matplotlib.use('Agg')

NEW_BUILDING_COLORS = ['orchid', 'plum', 'violet', 'thistle',
                       'lightpink', 'mediumorchid', 'hotpink']


def plot_parcel_boundary_lengths(parcel: ParcelDC, axes):
    # Logic to plot the side lengths
    # The parcel geometry boundary is always a MultiLineString.
    for line_string in parcel.geometry.boundary.geoms:
        x, y = line_string.coords.xy
        line_segments = [LineString([(x[i], y[i]), (x[i + 1], y[i + 1])])
                         for i in range(len(x) - 1)]

        for line in line_segments:
            # Only plot side lengths if they're not super short (like if they're parts)
            # of a curve.
            if line.length > 2.5:
                axes.annotate(text="{:.0f}m".format(line.length),
                              xy=line.centroid.coords[:][0],
                              ha='center')


def plot_new_buildings(parcel: ParcelDC, buildings: GeoDataFrame, utm_crs: pyproj.CRS,
                       address: str, topos: GeoDataFrame,
                       too_high_topos: GeoDataFrame, too_low_topos: GeoDataFrame,
                       new_buildings: list[Polygon],
                       open_space_poly: Polygonal, street_edges: MultiLineString,
                       flag_poly: Union[Polygon, None]):

    fig = plt.figure(f"new_buildings-{parcel.model.apn}")
    ax = fig.add_subplot()
    plt.title(parcel.model.apn + ':' + address)

    # Create the lot dataframe, which contains the parcel outline and existing buildings
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry.boundary], crs=utm_crs)
    lot_df.plot(ax=ax)

    plot_parcel_boundary_lengths(parcel, ax)

    if not topos.empty:
        topos.plot(ax=ax, color='gray')

    if not too_high_topos.empty:
        too_high_topos.plot(ax=ax, color='red')

    if not too_low_topos.empty:
        too_low_topos.plot(ax=ax, color='purple')

    geopandas.GeoSeries(open_space_poly).plot(ax=ax, alpha=0.4,
                                              color="lightgrey", edgecolor="green", hatch="..")

    geopandas.GeoSeries(street_edges.buffer(0.4)).plot(ax=ax, color='brown')

    # Plot new buildings
    for idx, poly in enumerate(new_buildings):
        geopandas.GeoSeries(poly).plot(
            ax=ax, color=NEW_BUILDING_COLORS[idx % len(NEW_BUILDING_COLORS)], alpha=0.6)

        ax.annotate(text="${:.0f}ft^2$".format(poly.area * 10.7639),
                    xy=poly.representative_point().coords[:][0],
                    ha='center')

    if flag_poly is not None:
        geopandas.GeoSeries(flag_poly).plot(ax=ax, color='cyan', alpha=0.2)
    return fig


def plot_split_lot(parcel: ParcelDC, address: str, buildings: GeoDataFrame, utm_crs: pyproj.CRS, second_lot: Polygonal):
    fig = plt.figure(f"lot_split-{parcel.model.apn}")
    ax = fig.add_subplot()
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry.boundary], crs=utm_crs)
    lot_df.plot(ax=ax)
    plot_parcel_boundary_lengths(parcel, ax)
    plt.title("Lot split: " + parcel.model.apn + ';' + address)
    geopandas.GeoSeries(second_lot).plot(
        ax=ax, color='cyan', alpha=0.7)

    return fig


def plot_cant_build(parcel: ParcelDC, address: str, buildings: GeoDataFrame, utm_crs: pyproj.CRS,
                    buffered_buildings: Polygonal, setbacks: list[Polygonal], too_steep: list[Polygonal],
                    flag_poly: Union[Polygon, None], street_edges: MultiLineString):
    fig = plt.figure(f"cant_build-{parcel.model.apn}")
    ax = fig.add_subplot()
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry.boundary], crs=utm_crs)
    lot_df.plot(ax=ax)
    plt.title("Cant build: " + parcel.model.apn + ';' + address)

    geopandas.GeoSeries(street_edges.buffer(0.4)).plot(
        ax=ax, color='brown')

    geopandas.GeoSeries(buffered_buildings).plot(
        ax=ax, color='cyan', alpha=0.7)

    if too_steep:
        # We only want to plot the parts of too_steep that are intersecting with parcel
        too_steep_intersecting = unary_union(
            too_steep).intersection(parcel.geometry)
        geopandas.GeoSeries(too_steep_intersecting).plot(
            ax=ax, color='red', alpha=0.7)

    for poly in setbacks:
        if not poly.is_empty:
            geopandas.GeoSeries(poly).plot(
                ax=ax, color='orange', alpha=0.7)

    if flag_poly:
        geopandas.GeoSeries(flag_poly).plot(
            ax=ax, color='green', alpha=0.3)

    return fig
