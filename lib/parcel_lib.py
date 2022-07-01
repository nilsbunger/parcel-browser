import geopandas
import shapely
from shapely.geometry import Polygon, box, MultiPolygon
from django.core.serializers import serialize
import json
from shapely.geometry import GeometryCollection
from shapely.ops import triangulate
# from notebooks.notebook_util import nb_exit
# Find rectangles based on another answer at
# https://stackoverflow.com/questions/7245/puzzle-find-largest-rectangle-maximal-rectangle-problem

from rasterio import features, transform, plot as rasterio_plot
from world.models import Parcel, ZoningBase, BuildingOutlines


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


def parcel_to_utm_gdf(parcel):
    """Converts a parcel into a UTM projection, stored as a Dataframe. This is a flat projection
    where one unit is one meter.

    Args:
        parcel (Parcel): The parcel to convert

    Returns:
        GeoDataFrame: A GeoDataFrame representing the parcel
    """
    serialized_parcel = serialize('geojson', [parcel], geometry_field='geom', )
    parcel_data_frame = geopandas.GeoDataFrame.from_features(
        json.loads(serialized_parcel), crs="EPSG:4326")
    return parcel_data_frame.to_crs(
        parcel_data_frame.estimate_utm_crs())


def buildings_to_utm_gdf(buildings):
    """Converts buildings into  UTM projections, stored as a Dataframe. This is a flat projection
    where one unit is one meter.

    Args:
        buildings ([BuildingOutlines]): A list of building outlines to convert

    Returns:
        GeoDataFrame: A GeoDataFrame representing the list of buildings
    """
    serialized_buildings = serialize(
        'geojson', buildings, geometry_field='geom', fields=('apn', 'geom',))
    buildings_data_frame = geopandas.GeoDataFrame.from_features(
        json.loads(serialized_buildings), crs="EPSG:4326")
    return buildings_data_frame.to_crs(
        buildings_data_frame.estimate_utm_crs())


# Moves parcel bounds to (0,0) for easier displaying
# Converts buildings into line strings?
def normalize_geometries(parcel, buildings):
    """Normalizes the parcel and buildings to (0,0).

    Args:
        parcel (GeoDataFrame): The parcel in a UTM-projected Dataframe
        buildings (GeoDataFrame): The buildings in a UTM-projected Dataframe

    Returns:
        A tuple containing the normalized parcel and buildings (parcel, building (ONE FOR NOW))
    """
    offset_bounds = parcel.total_bounds

    # move parcel coordinates to be 0,0 based so they're easier to see.
    parcel_boundary_multipoly = parcel.translate(
        xoff=-offset_bounds[0], yoff=-offset_bounds[1])[0]
    zero_bounds = parcel_boundary_multipoly.bounds

    # Change x in buildings.boundary[x] to support multiple buildings
    building_line_string = buildings.boundary[1].geoms[0]
    # move building coordinates to be 0,0 based so they're easier to see.
    building_line_string = shapely.affinity.translate(
        building_line_string, xoff=-offset_bounds[0], yoff=-offset_bounds[1])
    return (parcel_boundary_multipoly, building_line_string)


def get_avail_geoms(parcel_boundary_multipoly, building_line_string):
    """Returns a MultiPolygon representing the available space for a given parcel

    Args:
        parcel_boundary_multipoly (type?): A parcel
        building_line_string (type?): A LineString of a building in question (eventually will support
        multiple buildings)

    Returns:
        MultiPolygon: A multipolygon of the available space for placing ADUs/extra buildings
    """
    triags = triangulate(GeometryCollection(
        [building_line_string, parcel_boundary_multipoly]))

    # Find triangles not in the building:
    # DE-9IM gives a 3x3 matrix of how two objects relate. It's quite fascinating.
    # Check out the diagram in https://postgis.net/workshops/postgis-intro/de9im.html
    de9im = [x.relate(building_line_string.convex_hull)
             for idx, x in enumerate(triags)]
    kept_triangles = [x for idx, x in enumerate(
        triags) if de9im[idx][0] == 'F']
    # Why do we have the kept_triangles_gs?
    kept_triangles_gs = geopandas.GeoSeries(kept_triangles)

    return MultiPolygon(kept_triangles)


def find_largest_rectangles_on_avail_geom(avail_geom, num_rects):
    """Finds a number of the largest rectangles we can place given the available geometry.

    Args:
        avail_geom (MultiPolygon): The available geometry to place extra structures
        num_rects (int): The number of rectangles to find

    Returns:
        A list of biggest rectangles
    """
    placed_polys = []

    # Placement approach: Place single biggest unit, then rerun analysis
    for i in range(num_rects):    # place 4 units
        biggest_poly = biggestPolyOverRotations(avail_geom)
        placed_polys.append(biggest_poly)
        avail_geom = avail_geom.difference(MultiPolygon([biggest_poly]))

    return placed_polys


""" Find maximal rectangles in a grid
Returns: dictionary keyed by (x,y) of bottom-left, with values of (area, ((x,y),(x2,y2))) """
def maximalRectangles(matrix):
    m = len(matrix)
    n = len(matrix[0])
    # print (f'{m}x{n} grid (MxN)')
    cur_bot = 0
    cur_top=0

    left = [0] * n # initialize left as the leftmost boundary possible
    right = [n] * n # initialize right as the rightmost boundary possible
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
                if height[j]==1:
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
            if matrix[i][j] == 1: left[j] = max(left[j], cur_left)
            else:
                left[j] = 0
                cur_left = j + 1
        # update right
        for j in range(n-1, -1, -1):
            if matrix[i][j] == 1: right[j] = min(right[j], cur_right)
            else:
                right[j] = n
                cur_right = j
        # update the area
        for j in range(n):
            proposedarea = height[j] * (right[j] - left[j])
            rect = ((left[j], bot[j]), (right[j]-1, top[j]))
            if (height[j] >=2):
                if((rect[0]) not in dictrects) or (dictrects[rect[0]][0] < proposedarea):
                    dictrects[rect[0]] = (proposedarea, rect)
                bigrects.append((proposedarea, rect))
            if (proposedarea > maxarea):
                maxarea = proposedarea
                # bigrects.append([proposedarea, rect])


    bigrects = set(bigrects)

    return dictrects

""" Rotate grid from 0-90 degrees looking for best placement, and return a Polygon object of best placement"""
def biggestPolyOverRotations(avail_geom, do_plots=False):
    # print (avail_geom)
    biggest_area = 0
    biggest_rect = None
    for rot in [0, 10, 20, 30, 40, 50, 60, 70, 80]:
        rot_geom = shapely.affinity.rotate(avail_geom, rot, origin=(0,0))
        bounds = features.bounds(geopandas.GeoSeries(rot_geom))
        # print ("Bounds:", bounds)
        translation_amount = bounds
        rot_geom_translated = shapely.affinity.translate(rot_geom, xoff=-bounds[0], yoff=-bounds[1])
        bounds = features.bounds(geopandas.GeoSeries(rot_geom_translated))
        assert (bounds[0:2] == (0,0)) # bottom-left corner should be 0,0

        # print ("Bounds:", bounds)
        raster_dims = [round(bounds[3]),round(bounds[2])] # NOTE: raster_dims are Y,X
        b = features.rasterize([rot_geom_translated], raster_dims,) # transform=transform)

        if (do_plots):
            p2 = geopandas.GeoSeries().plot()
            rasterio_plot.show(b)
            p2.set_title(f'{rot} deg; raster')

        bigrects = maximalRectangles(b)
        sorted_keys = sorted(bigrects.keys(),key=lambda k: bigrects[k][0], reverse=True)
        rectarea, rectbounds = bigrects[sorted_keys[0]]
        # print ("Biggest rect:", rectarea, rectbounds)
        rect=box(rectbounds[0][0], rectbounds[0][1], rectbounds[1][0], rectbounds[1][1])
        if (do_plots):
            p1 = geopandas.GeoSeries(rot_geom_translated).plot()
            geopandas.GeoSeries(rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; rot+xlat map')

        rect = shapely.affinity.translate(rect, xoff=translation_amount[0], yoff=translation_amount[1])
        rect = shapely.affinity.rotate(rect, -rot, origin=(0,0))
        if (rectarea > biggest_area):
            biggest_area = rectarea
            biggest_rect = rect
        if (do_plots):
            p1 = geopandas.GeoSeries(avail_geom).plot()
            geopandas.GeoSeries(rect).plot(ax=p1, color='green')
            p1.set_title(f'{rot} deg; unrotated back')
    # Adjust positions by 0.5 to counteract quantization of raster.
    biggest_rect = shapely.affinity.translate(biggest_rect, xoff=0.5, yoff=0.5)

    return biggest_rect
