import geopandas
import shapely
from shapely.geometry import Polygon, box, MultiPolygon
from notebooks.notebook_util import nb_exit
## Find rectangles based on another answer at
## https://stackoverflow.com/questions/7245/puzzle-find-largest-rectangle-maximal-rectangle-problem

from rasterio import features, transform, plot as rasterio_plot

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
    return biggest_rect
