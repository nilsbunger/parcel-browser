import geopandas
import shapely
from shapely.geometry import Polygon, box, MultiPolygon
from django.core.serializers import serialize
import json
from shapely.geometry import GeometryCollection
from shapely.ops import triangulate
# Find rectangles based on another answer at
# https://stackoverflow.com/questions/7245/puzzle-find-largest-rectangle-maximal-rectangle-problem

from rasterio import features, transform, plot as rasterio_plot

from world.models import Parcel, ZoningBase, BuildingOutlines


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


def get_parcel(apn: str):
    """Returns a Parcel object from the database

    Args:
        apn (str): The APN of the parcel

    Returns:
        A Django Parcel model object
    """
    return Parcel.objects.get(apn=apn)


def get_buildings(parcel):
    """Returns a list of BuildingOutlines objects from the database that intersect with
    the given parcel object.

    Args:
        parcel (Parcel): Parcel object to intersect buildings with

    Returns:
        A list of BuildingOutlines objects
    """
    return BuildingOutlines.objects.filter(geom__intersects=parcel.geom)


def models_to_utm_gdf(models):
    """Converts a list of Django models into UTM projections, stored as a Dataframe.
    This is a flat projection where one unit is one meter.

    Args:
        models ([Model]): A list of Django models to convert

    Returns:
        GeoDataFrame: A GeoDataFrame representing the list of models
    """
    serialized_models = serialize(
        'geojson', models, geometry_field='geom', fields=('apn', 'geom',))
    data_frame = geopandas.GeoDataFrame.from_features(
        json.loads(serialized_models), crs="EPSG:4326")
    return data_frame.to_crs(data_frame.estimate_utm_crs())


# Moves parcel bounds to (0,0) for easier displaying
# Converts buildings into line strings?
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
        assert(len(translated_building_multipoly.geoms) == 1)

        building_polys.append(translated_building_multipoly[0])

    return (parcel_boundary_poly, building_polys)


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


def get_avail_geoms(parcel_geom, cant_build_geom):
    """Returns a MultiPolygon representing the available space for a given parcel

    Args:
        parcel_geom (Geometry): The geometry of a given parcel
        cant_build_geom (Geometry): The geometry of the area we can't build. This should
        be the union of buildings, setbacks, steep sections, etc.

    Returns:
        Multipolygon: A Multipolygon of the available space for placing ADUs/extra buildings
    """
    return parcel_geom.difference(cant_build_geom)


def find_largest_rectangles_on_avail_geom(avail_geom, num_rects, max_aspect_ratio=None):
    """Finds a number of the largest rectangles we can place given the available geometry.

    Args:
        avail_geom (MultiPolygon): The available geometry to place extra structures
        num_rects (int): The number of rectangles to find
        max_aspect_ratio (int or None): Maximum aspect ratio of rectangles to return

    Returns:
        A list of biggest rectangles
    """
    placed_polys = []

    # Placement approach: Place single biggest unit, then rerun analysis
    for i in range(num_rects):    # place 4 units
        biggest_poly = biggest_poly_over_rotation(
            avail_geom, max_aspect_ratio=max_aspect_ratio)
        placed_polys.append(biggest_poly)
        avail_geom = avail_geom.difference(MultiPolygon([biggest_poly]))

    return placed_polys


def get_buffered_building_geom(buildings):
    """Returns the geometry of buildings that's buffered by a certain width.

    Args:
        buildings (GeoDataFrame): The buildings in a UTM-projected Dataframe

    Returns:
        Geometry: A geometry (Polygon or MultiPolygon) representing the buffered buildings
    """
    # Buffer sizes according to building type, in meters
    BUFFER_SIZES = {
        "MAIN": 2,
        "ACCESSORY": 1.1,
        "ENCROACHMENT": 0.2,
    }
    return buildings.dissolve().buffer(BUFFER_SIZES["ACCESSORY"], cap_style=2, join_style=2)


""" Find maximal rectangles in a grid
Returns: dictionary keyed by (x,y) of bottom-left, with values of (area, ((x,y),(x2,y2))) """


def maximal_rectangles(matrix):
    m = len(matrix)
    n = len(matrix[0])
    # print (f'{m}x{n} grid (MxN)')
    cur_bot = 0
    cur_top = 0

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
        for j in range(n-1, -1, -1):
            if matrix[i][j] == 1:
                right[j] = min(right[j], cur_right)
            else:
                right[j] = n
                cur_right = j
        # update the area
        for j in range(n):
            proposedarea = height[j] * (right[j] - left[j])
            rect = ((left[j], bot[j]), (right[j]-1, top[j]))
            if (height[j] >= 2):
                if((rect[0]) not in dictrects) or (dictrects[rect[0]][0] < proposedarea):
                    dictrects[rect[0]] = (proposedarea, rect)
                bigrects.append((proposedarea, rect))
            if (proposedarea > maxarea):
                maxarea = proposedarea
                # bigrects.append([proposedarea, rect])

    bigrects = set(bigrects)

    return dictrects


def biggest_poly_over_rotation(avail_geom, do_plots=False, max_aspect_ratio=None):
    """Find an approximately biggest rectangle that can be placed in an available space at arbitrary rotation

    Args:
        avail_geom (MultiPolygon): The available geometry to place the rectangle
        do_plots (boolean): Plot intermediate steps (primarily for debugging
        max_aspect_ratio (int or None): Maximum aspect ratio of rectangles to return

    Returns:
        Polygon: The biggest rectangle fuound
    """
    # print (avail_geom)
    biggest_area = 0
    biggest_rect = None
    # Rotate grid from 0-90 degrees looking for best placement
    for rot in [0, 10, 20, 30, 40, 50, 60, 70, 80]:
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
        b = features.rasterize([rot_geom_translated], raster_dims,)

        if (do_plots):
            p2 = geopandas.GeoSeries().plot()
            rasterio_plot.show(b)
            p2.set_title(f'{rot} deg; raster')

        # Run the algorithm finding biggest rectangles at each candidate X,Y position
        bigrects = maximal_rectangles(b)
        # sort by area, from biggest to smallest
        sorted_keys = sorted(
            bigrects.keys(), key=lambda k: bigrects[k][0], reverse=True)
        # filter out rects which violate our optional aspect ratio constraint
        if (max_aspect_ratio):
            sorted_keys = [k for k in sorted_keys if aspect_ratio(
                bigrects[k][1]) <= max_aspect_ratio]
        rectarea, rectbounds = bigrects[sorted_keys[0]]
        # print ("Biggest rect:", rectarea, rectbounds)
        rect = box(rectbounds[0][0], rectbounds[0][1],
                   rectbounds[1][0], rectbounds[1][1])
        if (do_plots):
            p1 = geopandas.GeoSeries(rot_geom_translated).plot()
            geopandas.GeoSeries(rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; rot+xlat map')

        if (rectarea > biggest_area):
            biggest_area = rectarea
            biggest_rect = rect
            biggest_rect_rot = rot
            biggest_rect_xlat_amount = translation_amount
        if (do_plots):
            p1 = geopandas.GeoSeries(avail_geom).plot()
            plot_rect = shapely.affinity.translate(
                rect, xoff=translation_amount[0], yoff=translation_amount[1])
            plot_rect = shapely.affinity.rotate(rect, -rot, origin=(0, 0))
            geopandas.GeoSeries(plot_rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; unrotated back')
    # translate the biggest rect back into grid coordinates, undoing rotation and translation
    # Add in a 0.5 to counteract quantization of raster.
    biggest_rect = shapely.affinity.translate(
        biggest_rect, xoff=biggest_rect_xlat_amount[0]+0.5, yoff=biggest_rect_xlat_amount[1]+0.5
    )
    biggest_rect = shapely.affinity.rotate(
        biggest_rect, -biggest_rect_rot, origin=(0, 0))

    return biggest_rect
