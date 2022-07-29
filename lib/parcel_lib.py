from typing import List, Union
from lib.shapely_lib import multi_line_string_split

import django.contrib.gis.geos
import geopandas
import pyproj
import shapely
from django.db.models import QuerySet
from geopandas import GeoDataFrame, GeoSeries
from lib.types import ParcelDC, Polygonal
from shapely import wkt
from shapely.validation import make_valid
from shapely.ops import unary_union
from shapely.geometry import Polygon, box, MultiPolygon, LineString, MultiPoint, GeometryCollection
from django.core.serializers import serialize
import json
from shapely.geometry import MultiLineString, Point
from math import sqrt

from django.contrib.gis.geos import GEOSGeometry

from rasterio import features, plot as rasterio_plot
import shapely.ops

from world.models import Parcel, BuildingOutlines, ParcelSlope, ZoningBase

from numpy import argmax, argmin


def aspect_ratio(extents):
    """Calculate the aspect ratio of a rectangle

    Args:
        extents ((x1,y1), (x2,y2)): The extents of the rectangle as a tuple

    Returns:
        A float of the aspect ratio
    """
    (pt1, pt2) = extents
    w = pt2[0] - pt1[0] + 1
    h = pt2[1] - pt1[1] + 1
    aspect = max(float(w) / h, float(h) / w)
    return aspect


def get_parcel_by_apn(apn: str) -> Parcel:
    """Returns a Parcel object from the database

    Args:
        apn (str): The APN of the parcel

    Returns:
        A Django Parcel model object
    """
    return Parcel.objects.get(apn=apn)


def get_parcels_by_zip_codes(zip_codes: List) -> QuerySet:
    # Returns a Queryset of parcels that are in the provided list of zip codes,
    # and are not marked as skip in our analyzed table (so they are residential and match our criteria).
    # Results are ordered by APN so there's a consistent analysis order (and can thus start midway if needed).
    # NOTE: We should create a foreign key relationship so we don't need this ugly query.
    query = '|'.join(str(zip_code) for zip_code in zip_codes)
    return Parcel.objects.filter(situs_zip__regex=f'^({query})').extra(
        tables=['world_analyzedparcel'],
        where=['world_parcel.apn=world_analyzedparcel.apn',
               'world_analyzedparcel.skip is false']
    ).order_by('apn')


def get_parcels_by_neighborhood(bounding_box: django.contrib.gis.geos.GEOSGeometry) -> QuerySet:
    # Returns a Queryset of parcels that intersect with the bounding box (are in a neighborhood)
    # and are not marked as skip in our analyzed table (so they are residential and match our criteria).
    # Results are ordered by APN so there's a consistent analysis order (and can thus start midway if needed).
    # NOTE: We should create a foreign key relationship so we don't need this ugly query.

    return Parcel.objects.filter(geom__intersects=bounding_box).extra(
        tables=['world_analyzedparcel'],
        where=['world_parcel.apn=world_analyzedparcel.apn',
               'world_analyzedparcel.skip is false']
    ).order_by('apn')


def get_buildings(parcel: Parcel) -> QuerySet:
    """Returns a list of BuildingOutlines objects from the database that intersect with
    the given parcel object.

    Args:
        parcel (Parcel): Parcel object to intersect buildings with

    Returns:
        A list of BuildingOutlines objects
    """
    return BuildingOutlines.objects.filter(geom__intersects=parcel.geom)


def get_parcel_zone(parcel: ParcelDC, utm_crs: pyproj.CRS) -> str:
    """Gets the zone of a parcel.

    Args:
        parcel(ParcelDC)

    Returns:
        str: The zone of the parcel
    """
    zones = ZoningBase.objects.filter(geom__intersects=parcel.model.geom)

    if (len(zones)) == 1:
        return zones[0].zone_name
    elif (len(zones)) == 2:
        # We're ont he boundary of two zones. Find the one with the most overlap with parcel.
        zones_df = models_to_utm_gdf(zones, utm_crs)
        max_intersect_index = argmax(
            [geom.intersection(parcel.geometry).area for geom in zones_df.geometry])
        return zones[int(max_intersect_index)].zone_name
    else:
        raise Exception("Parcel has more than two zones")


def models_to_utm_gdf(
        models: list[django.contrib.gis.db.models],
        utm_crs: pyproj.CRS,
        geometry_field: str = 'geom') -> GeoDataFrame:
    """Converts a list of Django models into UTM projections, stored as a Dataframe.
    This is a flat projection where one unit is one meter.

    Args:
        models ([Model]): A list of Django GIS models to convert
        utm_crs: The destination projection
        geometry_field (str): The field that stores the geometry

    Returns:
        GeoDataFrame: A GeoDataFrame representing the list of models
    """
    if len(models) == 0:
        return geopandas.GeoDataFrame(columns=['feature'], geometry='feature')
    serialized_models = serialize(
        'geojson', models, geometry_field=geometry_field, fields=(geometry_field,))
    data_frame = geopandas.GeoDataFrame.from_features(
        json.loads(serialized_models), crs="EPSG:4326")
    df: GeoDataFrame = data_frame.to_crs(utm_crs)

    # Now, attach the original model objects to the GeoDataFrame
    df['model'] = models

    # Temporarily, make sure our dataframe translated correctly by comparing it to how we used
    # to do it. We can remove this after we've run some cycles with it.
    df_old = data_frame.to_crs(data_frame.estimate_utm_crs())
    assert ((df['geometry'] == df_old['geometry']).all())

    return df


def parcel_model_to_utm_dc(parcel_model: Parcel, utm_crs: pyproj.CRS) -> ParcelDC:
    """Converts a Parcel model into the ParcelDC dataclass object.

    Args:
        parcel_model (Parcel): A Parcel model to convert
        utm_crs: The destination projection

    Returns:
        GeoDataFrame: A GeoDataFrame representing the Parcel model
    """
    df = models_to_utm_gdf([parcel_model], utm_crs)
    return ParcelDC(df.geometry[0], df.model[0])


def polygon_to_utm(poly: django.contrib.gis.geos.GEOSGeometry, utm_crs: pyproj.CRS):
    """ Accepts a Django (gis.geos.*) geometry object in Lat-long coordinates, and returns
        an equivalent Shapely geometry object (shapely.geometry.*) suitable for use with GeoDjango,
         projected into 'crs' coordinates (typically UTM, created like this: CRS(proj='utm', zone=11, ellps='WGS84'))
    """
    # Convert Django polygon to Shapely polygon via well-known text
    shapely_poly = wkt.loads(poly.wkt)

    # Re-project the polygon into the UTM CRS coordinate system
    wgs84 = pyproj.CRS('EPSG:4326')
    projection = pyproj.Transformer.from_crs(
        wgs84, utm_crs, always_xy=True).transform
    return shapely.ops.transform(projection, shapely_poly)


def normalize_geometries(parcel, buildings):
    """Normalizes the parcel and buildings to (0,0).

    Args:
        parcel (GeoDataFrame): The parcel in a UTM-projected Dataframe
        buildings (GeoDataFrame): The buildings in a UTM-projected Dataframe

    Returns:
        A tuple containing the normalized parcel and buildings
        (parcel (Polygon), buildings ([Polygon]))
    """
    offset_bounds = parcel.total_bounds

    # move parcel coordinates to be 0,0 based so they're easier to see.
    parcel_boundary_multipoly = parcel.translate(
        xoff=-offset_bounds[0], yoff=-offset_bounds[1])[0]
    parcel_boundary_poly = parcel_boundary_multipoly[0]

    # translated is a list of buildings, each building represented as a MultiPolygon
    # Most MultiPolygons will have just one Polygon. Not sure which ones will have multiple
    # as it makes sense that one building is one polygon
    building_polys = []
    for building_geom in buildings.geometry:
        # This function returns the translated building as a multipolygon
        # However, a building should be only one polygon, and so we assert this
        # for a sanity check.
        translated_building_multipoly = shapely.affinity.translate(
            building_geom, xoff=-offset_bounds[0], yoff=-offset_bounds[1])
        assert (len(translated_building_multipoly.geoms) == 1)

        building_polys.append(translated_building_multipoly[0])

    return parcel_boundary_poly, building_polys


def collapse_multipolygon_list(multipolygons):
    """Collapses a list of multipolygons into one multipolygon

    Args:
        multipolygons ([MultiPolygon]): A list of multipolygons

    Returns:
        MultiPolygon: A single MultiPolygon
    """
    # TODO: Make this sexy with one list comprehension
    res = []
    for multipolygon in multipolygons:
        res.append(*multipolygon.geoms)
    return MultiPolygon(res)


def get_avail_geoms(parcel_geom: MultiPolygon, cant_build_geom: Polygonal) -> Polygonal:
    """Returns a MultiPolygon representing the available space for a given parcel

    Args:
        parcel_geom (Geometry): The geometry of a given parcel
        cant_build_geom (Geometry): The geometry of the area we can't build. This should
        be the union of buildings, setbacks, steep sections, etc.

    Returns:
        Multipolygon: A Multipolygon of the available space for placing ADUs/extra buildings
    """
    return parcel_geom.difference(cant_build_geom)


# Find rectangles based on an answer at
# https://stackoverflow.com/questions/7245/puzzle-find-largest-rectangle-maximal-rectangle-problem


def find_largest_rectangles_on_avail_geom(avail_geom: Polygonal, parcel_geom: Polygonal, num_rects,
                                          max_aspect_ratio=None, min_area: float = 0,
                                          max_total_area=float("inf"), max_area_per_building=float("inf")) \
        -> List[Polygon]:
    """Finds a number of the largest rectangles we can place given the available geometry. If a minimum
    or maximum area are passed in, the rectangle sizes will be within that area. If not enough rectangles
    meet the minimum size, then only n < num_rects number of rectangles will be returned.

    Args:
        avail_geom (MultiPolygon): The available geometry to place extra structures
        parcel_geom (MultiPolygon): A geometry representing the boundary of the parcel
        or exterior of the parcel.
        num_rects (int): The number of rectangles to find
        max_aspect_ratio (int or None): Maximum aspect ratio of rectangles to return
        min_area (num or None): Minimum area of a building in square meters
        max_area_per_building (num or None): Maximum area of a building in square meters

    Returns:
        A list of biggest rectangles found.
    """
    placed_polys = []

    # Placement approach: Place single biggest unit, then rerun analysis
    for i in range(num_rects):  # place 4 units
        if max_total_area < min_area:
            break
        biggest_poly = biggest_poly_over_rotation(
            avail_geom, parcel_geom.boundary, max_aspect_ratio=max_aspect_ratio,
            min_area=min_area, max_area=min(max_total_area, max_area_per_building))

        if biggest_poly is None:
            break

        placed_polys.append(biggest_poly)
        avail_geom = avail_geom.difference(
            MultiPolygon([biggest_poly]))
        max_total_area -= biggest_poly.area

    return placed_polys


def get_street_side_boundaries(parcel: ParcelDC, utm_crs: pyproj.CRS) \
        -> tuple[MultiLineString, MultiLineString, MultiLineString]:
    """ Returns the edges of a parcel that are on the street side, the sides of the lot,
    and the back of the lot respectively as Shapely MultiLineStrings.
    Function can be greatly improved with road data, and other types of data we can
    layer on top.

    Args:
        parcel (ParcelDC): A Django Parcel model
        utm_crs: (pyproj.CRS): Coordinate system to use for analysis.
    Returns:
        (MultiLineString, MultiLineString, MultiLineString): A tuple of MultiLineStrings
        representing the front (street), side, and back edges respectively.
    """

    # Get our adjacent parcels
    intersecting_parcels = Parcel.objects.filter(
        geom__intersects=parcel.model.geom).exclude(apn=parcel.model.apn)
    intersecting_utm = models_to_utm_gdf(intersecting_parcels, utm_crs)

    # First Heuristic for determining street side:
    # The sides that intersect with other parcels are definetely not street side
    # Find the intersections between the adjacent parcels and the parcel
    other_parcels_geom = intersecting_utm.dissolve().geometry[0]
    parcels_intersection = other_parcels_geom.intersection(
        parcel.geometry)  # MultiLineString

    # The difference between the outline and the intersection is the street side
    # NOTE: this implementation to find the street side is not perfect. It's possible
    # that a side that doesn't have an adjacent parcel is the back of a lot, or just has
    # wilderness or something behind it.
    street_edges = parcel.geometry.boundary.difference(
        parcels_intersection)  # MultiLineString

    # The back is the union of all the line segments that don't touch any of the street edges
    # The lines that do touch are the sides.
    # TODO: Improve this with simplifying the line segments
    side_lines, back_lines = [], []

    # parcels_intersection is sometimes a LineString, convert it to a MultiLineString
    if isinstance(parcels_intersection, LineString):
        parcels_intersection = MultiLineString([parcels_intersection])

    for line in parcels_intersection.geoms:
        if line.intersects(street_edges):
            side_lines.append(line)
        else:
            back_lines.append(line)
    side_edges = MultiLineString(side_lines)
    back_edges = MultiLineString(back_lines)

    return street_edges, side_edges, back_edges


def get_setback_geoms(parcel_geom: MultiPolygon, setback_widths: tuple[float, float, float], edges):
    """Given setback widths and the front, side, and back edges, returns the geometry
    representing that setback.

    Args:
        parcel_geom (MultiPolygon): A MultiPolygon representing the parcel's geometry
        setback_widths ((float, float, float)): A tuple representing the setback widths (in meters)
        for the front (street), side, and back edges
        edges: ((MultiLineString, MultiLineString, MultiLineString)): A tuple representing the edges
        of the parcel. The front, side, and back edges.

    Returns:
        (Geometry, Geometry, Geometry): A tuple of Geometry representing the front, side, and back setbacks
    """
    setbacks = []
    for setback_width, edges in zip(setback_widths, edges):
        setback = edges.buffer(setback_width).intersection(parcel_geom)
        setbacks.append(setback)
    return setbacks


def identify_building_types(parcel_geom: Polygonal, buildings: GeoDataFrame) -> None:
    """Identify the building type (Accessory, main, or encroachment) of a building
    on a lot in-place

    Args:
        parcel_geom (Polygon or MultiPolygon): The geometry of the parcel that the buildings' on
        buildings (GeoDataFrame): The buildings to identify
    """
    # The percent of a building's area that must be inside the parcel
    # to be not considered an encroachment
    ENCROACHMENT_THRESHOLD = 0.4

    max_area = 0
    max_area_index = 0

    # Go through each building and label it's building_type appropriately
    for i, building in buildings.iterrows():
        if building.geometry.intersection(parcel_geom).area / building.geometry.area < ENCROACHMENT_THRESHOLD:
            buildings.loc[i, 'building_type'] = 'ENCROACHMENT'
        else:
            buildings.loc[i, 'building_type'] = 'ACCESSORY'

            if building.geometry.area > max_area:
                max_area = building.geometry.area
                max_area_index = i

    # Find the building with the max area that's not an encroachment and mark it as the main building
    buildings.loc[max_area_index, 'building_type'] = 'MAIN'


def get_avail_floor_area(parcel: ParcelDC, buildings: GeoDataFrame, max_FAR: float) -> float:
    """Returns the available floor area of a parcel in square meters such that
    the FAR constraints aren't violated. Uses the floor area as calculated by summing
    the garages and total living area that are on the model object. However, if total_lvg_field
    is missing, will default to use the floor area by building.

    Args:
        parcel (ParcelDC): The parcel the building is on
        buildings (GeoDataFrame): The buildings on the parcel
        max_FAR (float): The maximum floor area to return. < 1

    Returns:
        num: The available floor area to build in sqm. Must be > 0
    """
    # Get the total floor area of the existing buildings
    # for i, bldg in buildings.iterrows():
    #     print(bldg.building_type)

    if parcel.model.total_lvg_field:
        # Sqm. Assume each garage/carport is 23.2sqm, or approx. 250sqft
        num_garages = int(
            parcel.model.garage_sta) if parcel.model.garage_sta else 0
        num_carports = int(
            parcel.model.carport_st) if parcel.model.carport_st else 0
        garage_area = (num_garages + num_carports) * 23.2
        total_lvg_by_model = parcel.model.total_lvg_field / 10.764
        existing_floor_area = total_lvg_by_model + garage_area
    else:
        existing_floor_area = sum([
            bldg.geometry.area for i, bldg in buildings.iterrows() if bldg.building_type != "ENCROACHMENT"])

    return max(0, max_FAR * parcel.geometry.area - existing_floor_area)


def get_buffered_building_geom(buildings: GeoDataFrame, buffer_sizes) -> Polygonal:
    """Returns the geometry of buildings that's buffered by a certain width.

    Args:
        buildings (GeoDataFrame): The buildings in a UTM-projected Dataframe
        buffer_sizes (float): The width of the buffer to apply to the buildings

    Returns:
        Geometry: A geometry (Polygon or MultiPolygon) representing the buffered buildings
    """
    # TODO: Fix buffer sizes
    # Buffer sizes according to building type, in meters
    return buildings.dissolve().buffer(buffer_sizes["ACCESSORY"], cap_style=2, join_style=2)


def maximal_rectangles(matrix):
    """ Find maximal rectangles in a grid
    Returns: dictionary keyed by (x,y) of bottom-left, with values of (area, ((x,y),(x2,y2))) """
    m = len(matrix)
    n = len(matrix[0])
    # print (f'{m}x{n} grid (MxN)')

    left = [0] * n  # initialize left as the leftmost boundary possible
    right = [n] * n  # initialize right as the rightmost boundary possible
    height = [0] * n
    bot = [0] * n
    top = [0] * n

    maxarea = 0
    bigrects = []
    dictrects = {}
    for i in range(m):

        cur_left, cur_right = 0, n
        # update height
        for j in range(n):
            if matrix[i][j] == 1:
                height[j] += 1
                if height[j] == 1:
                    bot[j] = i
                    top[j] = i
                else:
                    top[j] = i
            else:
                height[j] = 0
                top[j] = i
                bot[j] = i
        # update left
        for j in range(n):
            if matrix[i][j] == 1:
                left[j] = max(left[j], cur_left)
            else:
                left[j] = 0
                cur_left = j + 1
        # update right
        for j in range(n - 1, -1, -1):
            if matrix[i][j] == 1:
                right[j] = min(right[j], cur_right)
            else:
                right[j] = n
                cur_right = j
        # update the area
        for j in range(n):
            proposedarea = height[j] * (right[j] - left[j])
            rect = ((left[j], bot[j]), (right[j] - 1, top[j]))
            if height[j] >= 2:
                if ((rect[0]) not in dictrects) or (dictrects[rect[0]][0] < proposedarea):
                    dictrects[rect[0]] = (proposedarea, rect)
                bigrects.append((proposedarea, rect))
            if proposedarea > maxarea:
                maxarea = proposedarea
                # bigrects.append([proposedarea, rect])

    return dictrects


def clamp_placed_polygon_to_size(big_rect, parcel_boundary, max_area, rotate_parcel_by, translate_parcel_by):
    """Takes an axis-aligned rectangle (big_rect) with area bigger than max_area, and shrinks it so that it's
    still within the bounds of big_rect, but with area as max_area. The algorithm will squish the rectangle
    to be as square as possible. If after squishing to a square, the size is still too big, then the square
    will be scaled down to max_area. The resulting rectangle/square will be placed in the corner that is
    closest to the parcel lot lines (so that polygons are "hugging" lot lines as much as possible).

    Args:
        big_rect (Polygon): A rectangle that we want to squish
        parcel_boundary (Geometry): A geometry (Polygon or Multipolygon) representing the boundary
        or exterior of the parcel.
        max_area (num): Maximum area of a building
        rotate_parcel_by (num): The angle (in degrees) to rotate the parcel boundary by to match the
        rotation of the big_rect.
        translate_parcel_by ((num, num)): A tuple (x, y) encoding how much to translate the parcel by
        so that it matches the translation of big_rect.

    Returns:
        Polygon: The scaled down rectangle with area max_area.
    """
    # We will first prioritize making it as square as possible, then scale down the square
    # if that's not enough
    minx, miny, maxx, maxy = big_rect.bounds
    x_len = maxx - minx
    y_len = maxy - miny
    if min(x_len, y_len) ** 2 > max_area:
        # See if the square area of the minor axis is bigger than the max. If so, we do a scaled down square
        # Scale down the square
        rect_to_place = shapely.affinity.scale(big_rect, xfact=(
            sqrt(max_area) / x_len), yfact=(sqrt(max_area) / y_len))
    elif x_len > y_len:
        # Squish the rectangle to the max_area
        # x is major axis. We want to scale it down
        rect_to_place = shapely.affinity.scale(
            big_rect, xfact=(max_area / big_rect.area))
    else:
        rect_to_place = shapely.affinity.scale(
            big_rect, yfact=(max_area / big_rect.area))

    # Rotate and translate the parcel's boundary geometry for analysis
    parcel_boundary = shapely.affinity.rotate(
        parcel_boundary, rotate_parcel_by, origin=(0, 0))
    parcel_boundary = shapely.affinity.translate(
        parcel_boundary, xoff=-translate_parcel_by[0], yoff=-translate_parcel_by[1])

    # Now that we've scaled the rectangle down, let's place it on the corner closest to lot lines

    # Find out which corner is the closest to the lot lines
    # four corners - lower left, upper left, upper right, lower right
    minx, miny, maxx, maxy = big_rect.bounds
    big_rect_four_corners = [(minx, miny), (minx, maxy),
                             (maxx, maxy), (maxx, miny)]
    minx, miny, maxx, maxy = rect_to_place.bounds
    to_place_four_corners = [(minx, miny), (minx, maxy),
                             (maxx, maxy), (maxx, miny)]

    # Find the closest corner of the bigger rectangle to the lot lines
    closest_corner_index = argmin(
        [Point(*corner).distance(parcel_boundary) for corner in big_rect_four_corners])

    # Now perform a translation that puts the building in the corner of the big
    # rectangle that's closest to lot lines. This lets our building "hug" the lot lines.
    # This frees up more available space for other buildings to be placed
    x_offset = big_rect_four_corners[closest_corner_index][0] - \
        to_place_four_corners[closest_corner_index][0]
    y_offset = big_rect_four_corners[closest_corner_index][1] - \
        to_place_four_corners[closest_corner_index][1]
    rect_to_place = shapely.affinity.translate(
        rect_to_place, xoff=x_offset, yoff=y_offset)

    return rect_to_place


def biggest_poly_over_rotation(avail_geom, parcel_boundary, do_plots=False, max_aspect_ratio=None,
                               min_area: float = 0, max_area=None):
    """Find an approximately biggest rectangle that can be placed in an available space at arbitrary rotation.
    Polygon sizes can be clamped with optional min_area or max_area parameters. In the event when the initial
    rectangle found exceeds the max_area, an algorithm will scale the rectangle down to max_area. See implementation
    of clamp_placed_polygon_to_size for details.

    Args:
        avail_geom (MultiPolygon): The available geometry to place the rectangle
        parcel_boundary (Geometry): A geometry (Polygon or Multipolygon) representing the boundary
        or exterior of the parcel.
        do_plots (boolean): Plot intermediate steps (primarily for debugging
        max_aspect_ratio (int or None): Maximum aspect ratio of rectangles to return
        min_area (num or None): Minimum area of a building
        max_area (num or None): Maximum area of a building

    Returns:
        Polygon: The biggest rectangle found, or None if no rectangle was found that adheres to min_area
    """
    # print (avail_geom)
    biggest_area = 0
    biggest_rect = None
    # Rotate grid from 0-90 degrees looking for best placement
    for rot in range(0, 90, 5):
        rot_geom = shapely.affinity.rotate(avail_geom, rot, origin=(0, 0))
        bounds = features.bounds(geopandas.GeoSeries(rot_geom))
        # print ("Bounds:", bounds)
        translation_amount = bounds
        rot_geom_translated = shapely.affinity.translate(
            rot_geom, xoff=-bounds[0], yoff=-bounds[1])
        bounds = features.bounds(geopandas.GeoSeries(rot_geom_translated))
        assert (bounds[0:2] == (0, 0))  # bottom-left corner should be 0,0

        # Rasterize the rotated avail_geom for the placement algorithm.
        raster_dims = [round(bounds[3]), round(bounds[2])
                       ]  # NOTE: raster_dims are Y,X
        # transform=transform)
        b = features.rasterize([rot_geom_translated], raster_dims, )

        if do_plots:
            p2 = geopandas.GeoSeries().plot()
            rasterio_plot.show(b)
            p2.set_title(f'{rot} deg; raster')

        # Run the algorithm finding biggest rectangles at each candidate X,Y position
        bigrects = maximal_rectangles(b)
        # sort by area, from biggest to smallest
        sorted_keys = sorted(
            bigrects.keys(), key=lambda k: bigrects[k][0], reverse=True)
        # filter out rects which violate our optional aspect ratio constraint
        if max_aspect_ratio:
            sorted_keys = [k for k in sorted_keys if aspect_ratio(
                bigrects[k][1]) <= max_aspect_ratio]

        if not sorted_keys:
            continue

        rectarea, rectbounds = bigrects[sorted_keys[0]]
        # print ("Biggest rect:", rectarea, rectbounds)
        rect = box(rectbounds[0][0], rectbounds[0][1],
                   rectbounds[1][0], rectbounds[1][1])
        if do_plots:
            p1 = geopandas.GeoSeries(rot_geom_translated).plot()
            geopandas.GeoSeries(rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; rot+xlat map')

        if rectarea > biggest_area:
            biggest_area = rectarea
            biggest_rect = rect
            biggest_rect_rot = rot
            biggest_rect_xlat_amount = translation_amount
        if do_plots:
            p1 = geopandas.GeoSeries(avail_geom).plot()
            plot_rect = shapely.affinity.translate(
                rect, xoff=translation_amount[0], yoff=translation_amount[1])
            plot_rect = shapely.affinity.rotate(plot_rect, -rot, origin=(0, 0))
            geopandas.GeoSeries(plot_rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; unrotated back')

    if max_area is not None and biggest_rect.area > max_area:
        # If it's too big, we want to do some processing to trim it down.
        biggest_rect = clamp_placed_polygon_to_size(
            biggest_rect, parcel_boundary, max_area, biggest_rect_rot, biggest_rect_xlat_amount)

    # If it's too small, we return None
    if biggest_rect.area < min_area:
        return None

    # translate the biggest rect back into grid coordinates, undoing rotation and translation
    # Translate by 0.5 to counteract quantization of raster.
    biggest_rect = shapely.affinity.translate(
        biggest_rect, xoff=biggest_rect_xlat_amount[0] + 0.5, yoff=biggest_rect_xlat_amount[1] + 0.5
    )
    biggest_rect = shapely.affinity.rotate(
        biggest_rect, -biggest_rect_rot, origin=(0, 0))

    return biggest_rect


def get_too_steep_polys(parcel_model: Parcel, utm_crs: pyproj.CRS, max_slope: int):
    """Gets the areas with a slope greater than the max_slope of a given parcel, returned as a multipolygon

    Args:
        parcel_model (Parcel): A Django Parcel model object
        utm_crs: (pyproj.CRS): Coordinate system to use for analysis.
        max_slope (int): The maximum slope to consider

    Returns:
        Multipolygon representing the area that's too steep
    """
    polys = ParcelSlope.objects.filter(
        polys__intersects=parcel_model.geom, grade__gt=max_slope)

    polys = models_to_utm_gdf(polys, utm_crs, geometry_field='polys').geometry

    # Make each poly valid
    # We need this because sometimes, the ParcelSlope polys are invalid geometries
    # We may want to go through all the ParcelSlope polys and correct the invalid ones/figure
    # out which ones are invalid
    polys = [make_valid(poly) for poly in polys]

    return polys


def get_second_lot(lots, main_building):
    return [lot for lot in lots if lot.intersection(main_building).area < .1][0]


def split_lot(parcel_geom: MultiPolygon, buildings: GeoDataFrame, target_second_lot_ratio: float = 0.5):
    main_building = [
        bldg.geometry for i, bldg in buildings.iterrows() if bldg.building_type == "MAIN"][0]

    # Turn the main building into a rectangle to simplify calculations
    min_rect = main_building.minimum_rotated_rectangle

    # Optional buffering - this is so we're not hugging the main building too tightly
    min_rect = min_rect.buffer(0.5, cap_style=2, join_style=2)

    # Turn the bounding box into lines
    x, y = min_rect.exterior.coords.xy
    bb_lines = [LineString([(x[i], y[i]), (x[i + 1], y[i + 1])])
                for i in range(len(x) - 1)]

    # Now calculate possibilities for a second parcel,
    # storing this into second_lots
    parcel_bounds = parcel_geom.boundary
    second_lots = []
    lines = []
    for line in bb_lines:
        # First, scale it up by a lot
        line = shapely.affinity.scale(line, 100, 100, 100)

        # Then find the intersections between the line and parcel boundary
        intersections = parcel_bounds.intersection(line)

        # Skip if there's no intersections, which means the line is outside the parcel
        if intersections.is_empty:
            continue

        # Should only intersect with 2 points. Draw a line using these intersections,
        # which effectively scales down our lines for easier drawing/debugging later on
        assert (len(intersections.geoms) == 2)
        line = LineString(intersections.geoms)
        line = shapely.affinity.scale(line, 1.1, 1.1, 1.1)

        lines.append(line)

        split = shapely.ops.split(parcel_geom, line)

        # Sanity check: Splitting it should only result in 2 polygons
        assert (len(split.geoms) == 2)

        # Now append the lot that doesn't have the main house. Allow a margin of error
        second_lots.append(
            get_second_lot(split.geoms, main_building))

    biggest_lot_index = argmax([lot.area for lot in second_lots])
    biggest_lot = second_lots[biggest_lot_index]
    biggest_lot_area_ratio = biggest_lot.area / parcel_geom.area

    # TODO: Consider L SHAPES if the lot is too small
    # If even the biggest lot we can get is too small, return None
    if biggest_lot_area_ratio < 0.4:
        return None, None

    # Let's try to cut down the size of the lot to target_second_lot_ratio via binary search
    line_to_move = lines[biggest_lot_index]
    if line_to_move.parallel_offset(0.01, 'left').intersects(biggest_lot):
        side = 'left'
    else:
        side = 'right'

    start = 0
    stop = max([line_to_move.distance(Point(point))
                for point in biggest_lot.exterior.coords])

    for i in range(15):
        mid = (start + stop) / 2
        new_div_line = line_to_move.parallel_offset(mid, side)
        new_div_line = shapely.affinity.scale(new_div_line, 100, 100, 100)

        # Divide the lot
        split = shapely.ops.split(parcel_geom, new_div_line)
        new_second_lot = get_second_lot(split.geoms, main_building)
        new_area_ratio = new_second_lot.area / parcel_geom.area

        if new_area_ratio > target_second_lot_ratio:
            start = mid
        else:
            stop = mid

    return new_second_lot, new_area_ratio


def identify_flag(parcel: ParcelDC, front_street_edge: Union[MultiLineString, LineString]) -> Union[Polygon, None]:
    """Will return a polygon representing the area of the "flag handle" if the lot is a flag.
    If it isn't, returns None. Uses Binary search to find when the length of the handle blows up,
    in which case we have the start and end points of the flag.

    Args:
        parcel (ParcelDC): The ParcelDC to identify
        front_street_edge (LineString): The edge of the front street

    Returns:
        Polygon: Representing the flag
    """
    # A flag is a lot that has a very small street frontage. This street frontage is less than
    # the minimum. Most lots have a minimum street frontage of 30 feet, so we picked 30.
    # NOTE: This could change in the future with more info. Tweak this to be right.
    # A flag's street-facing edge should also just be a straight line, so if it's a multi-line
    # string or a curve, it's not a flag
    MIN_STREET_FRONTAGE = 30 / 3.28
    if front_street_edge.length > MIN_STREET_FRONTAGE or \
            isinstance(front_street_edge, MultiLineString) or \
            len(front_street_edge.coords) > 2:
        return None

    # Find out which direction the lot is facing
    if front_street_edge.parallel_offset(0.01, 'left').intersects(parcel.geometry):
        side = 'left'
    else:
        side = 'right'

    seek_line = shapely.affinity.scale(front_street_edge, 100, 100, 100)

    start = 0
    stop = max([seek_line.distance(Point(point))
                for point in parcel.geometry.geoms[0].exterior.coords])

    # Use bianry search to seek until it gets to at least 1.3x the width, or until intersection turns into line
    for i in range(15):
        mid = (start + stop) / 2
        new_div_line = front_street_edge.parallel_offset(mid, side)
        new_div_line = shapely.affinity.scale(new_div_line, 100, 100, 100)

        intersection = new_div_line.intersection(parcel.geometry.boundary)

        # Has to be a multi-point, otherwise there's some weird behavior
        assert(isinstance(intersection, MultiPoint))

        # Find the minimum distance between points. If there's more than two points,
        # pick the two edges that are closest to front_street_edge. This is geometrically
        # guaranteed to be the edges that lie on the flag
        if len(intersection.geoms) > 2:
            points = list(intersection.geoms)
            points.sort(
                key=lambda x: front_street_edge.distance(x))
            flag_width = points[0].distance(points[1])
        else:
            flag_width = intersection.geoms[0].distance(intersection.geoms[1])

        if flag_width > 1.3 * front_street_edge.length:
            stop = mid
        else:
            start = mid

    # Now find out the part of the parcel that is a flag
    split = shapely.ops.split(parcel.geometry, new_div_line)

    # POSSIBLE BUG: Watch out for concave parcel shapes
    flag_poly = split.geoms[argmin([poly.area for poly in split.geoms])]

    return flag_poly


def get_too_high_or_low(parcel: ParcelDC, buildings: GeoDataFrame, topos: GeoDataFrame, utm_crs):
    # Elevations are in feet
    MAX_ELEV_DIFF = 20  # in feet
    # Ensure there are rows in the topos dataframe
    if topos.empty:
        return GeoDataFrame(), GeoDataFrame(), Polygon()

    main_building = [
        bldg.geometry for i, bldg in buildings.iterrows() if bldg.building_type == "MAIN"][0]

    # Find the elevation of the main building
    main_building_topo_index = argmin([main_building.centroid.distance(topo.geometry)
                                       for i, topo in topos.iterrows()])
    main_building_elev = topos.model[main_building_topo_index].elev
    # print(main_building_elev)

    max_elev = main_building_elev + MAX_ELEV_DIFF
    min_elev = main_building_elev - MAX_ELEV_DIFF

    # Get range of the elevations
    elev_list = [t.elev for t in topos.model]
    # If the ranges are within the main building elevation, nothing to be done
    if max(elev_list) < max_elev and min(elev_list) > min_elev:
        return GeoDataFrame(), GeoDataFrame(), Polygon()

    # print(sorted(elev_list))

    # Get rid of everything in the dataframe that's in the range, so we only have too high/low
    too_high = topos[[t.elev >= max_elev for t in topos.model]]
    too_low = topos[[t.elev <= min_elev for t in topos.model]]

    # Now check for the ones that are too high
    cant_build = Point()
    if not too_high.empty:
        i = argmin([t.elev for t in too_high.model])
        to_split = too_high.iloc[i].geometry
        if isinstance(to_split, MultiLineString):
            split_list = multi_line_string_split(parcel.geometry, to_split)
        else:
            split_list = shapely.ops.split(parcel.geometry, to_split).geoms
        # Just get the one without main building on it
        too_high_poly = [
            poly for poly in split_list if not poly.intersects(main_building)]
        cant_build = unary_union([cant_build, *too_high_poly])

    # Now check for the ones that are too low
    if not too_low.empty:
        i = argmax([t.elev for t in too_low.model])
        to_split = too_low.iloc[i].geometry
        if isinstance(to_split, MultiLineString):
            split_list = multi_line_string_split(parcel.geometry, to_split)
        else:
            split_list = shapely.ops.split(parcel.geometry, to_split).geoms
        too_low_poly = [
            poly for poly in split_list if not poly.intersects(main_building)]
        cant_build = unary_union([cant_build, *too_low_poly])

    return too_high, too_low, cant_build
