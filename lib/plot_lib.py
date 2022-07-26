# Helper functions to plot geographical data

from lib.parcel_lib import *
import geopandas
import matplotlib.pyplot as plt
from lib.types import ParcelDC
import pyproj

NEW_BUILDING_COLORS = ['orchid', 'plum', 'violet', 'thistle',
                       'lightpink', 'mediumorchid', 'hotpink']


def plot_new_buildings(parcel: ParcelDC, buildings: GeoDataFrame, utm_crs: pyproj.CRS,
                       address: str, topos: GeoDataFrame, new_buildings: list[Polygon],
                       open_space_poly: Polygonal, street_edges: MultiLineString,
                       flag_poly: Union[Polygon, None]):

    # Create the lot dataframe, which contains the parcel outline and existing buildings
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry.boundary], crs=utm_crs)

    # Plots a parcel, buildings, and new buildings
    fig = plt.figure("new_buildings")
    ax = fig.add_subplot()
    lot_df.plot(ax=ax)
    plt.title(parcel.model.apn + ':' + address)

    if not topos.empty:
        topos.plot(ax=ax, color='gray')
    geopandas.GeoSeries(open_space_poly).plot(ax=ax, alpha=0.4,
                                              color="lightgrey", edgecolor="green", hatch="..")

    geopandas.GeoSeries(street_edges.buffer(0.4)).plot(ax=ax, color='brown')

    # Plot new buildings
    for idx, poly in enumerate(new_buildings):
        geopandas.GeoSeries(poly).plot(
            ax=ax, color=NEW_BUILDING_COLORS[idx % len(NEW_BUILDING_COLORS)], alpha=0.6)

        plt.annotate(text="${:.0f}ft^2$".format(poly.area * 10.7639),
                     xy=poly.representative_point().coords[:][0],
                     ha='center')

    if flag_poly is not None:
        geopandas.GeoSeries(flag_poly).plot(ax=ax, color='cyan', alpha=0.2)
    return fig


def plot_split_lot(parcel: ParcelDC, address: str, buildings: GeoDataFrame, utm_crs: pyproj.CRS, second_lot: Polygonal):
    fig = plt.figure("lot_split")
    ax = fig.add_subplot()
    lot_df = geopandas.GeoDataFrame(
        geometry=[*buildings.geometry, parcel.geometry.boundary], crs=utm_crs)
    lot_df.plot(ax=ax)
    plt.title("Lot split: " + parcel.model.apn + ';' + address)
    geopandas.GeoSeries(second_lot).plot(
        ax=ax, color='cyan', alpha=0.7)

    return fig
