import gc
import re
from typing import Dict

import django
import geopandas
import pyproj
import shapely
import matplotlib as mpl
from matplotlib import pyplot as plt
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

from lib.parcel_lib import get_parcels_by_neighborhood, models_to_utm_gdf, get_buildings, polygon_to_utm
from lib.shapely_lib import regularize_to_multipolygon, yield_interiors
from world.models import Topography, ParcelSlope, TopographyLoads, Parcel

colors = {25: 'red', 20: 'orange', 15: 'gold', 10: 'greenyellow', 5: 'springgreen', 0: 'white'}


def calculate_parcel_slopes(bounding_box: django.contrib.gis.geos.GEOSGeometry, utm_crs: pyproj.CRS, start_idx=0):
    """ Calculate slopes for all parcels within a bounding box that are in analyzed_parcel table without
        a 'skip' flag. Records slopes in the database. """
    # Prevent memory leak in matplotlib by using non-gui backend. see
    # https://github.com/matplotlib/matplotlib/issues/20300
    mpl.use('agg')

    topo_list = list(TopographyLoads.objects.values_list('extents', flat=True))
    topo_areas = django.contrib.gis.geos.MultiPolygon(topo_list)
    parcels = get_parcels_by_neighborhood(bounding_box)

    print(f'Analyzing {len(parcels)} parcels...')
    error_parcels = []
    bucket_stats = {'empty': 0, 'weird': 0, 'full': 0, 'no_buildings': 0, 'no_topos': 0}
    idx = 0
    for idx, parcel in enumerate(parcels.iterator(chunk_size=10)):
        if idx < start_idx: continue
        print(f'Index {idx}, apn={parcel.apn}. Slope Bucket Stats={bucket_stats}.'
              f' {bucket_stats["no_buildings"]} lots w/o buildings.'
              f' {bucket_stats["no_topos"]} sites without topos. {len(error_parcels)} errors')
        # print(f'Memory usage (MB):', tracemalloc.get_traced_memory()[0]/1e6, tracemalloc.get_traced_memory()[1]/1e6)
        try:
            # Make sure parcel we're analyzing has associated topo info
            if not _check_parcel_has_topo(parcel, topo_areas):
                bucket_stats["no_topos"] += 1
                continue
            # Close old plots to prevent memory growth
            plt.close("all")
            if idx % 10 == 0: gc.collect()

            topos = get_topo_lines(parcel)
            topos_df = models_to_utm_gdf(topos, utm_crs)
            plot = create_slopes_for_parcel(parcel, utm_crs, topos_df, bucket_stats)

            # Finalize parcel plot with slope data, and save plot image to file
            buildings = get_buildings(parcel)
            if len(buildings) > 0:
                buildings_df = models_to_utm_gdf(buildings, utm_crs)
                buildings_df.plot(ax=plot, )
            else:
                print("NO BUILDINGS ON LOT")
                bucket_stats["no_buildings"] += 1
            topos_df.plot(ax=plot, color='gray')
            plt.title('APN=' + str(parcel.apn))
            plt.savefig("./world/data/topo-images/" + parcel.apn + ".jpg")
        except Exception as e:
            print(f"ERROR in parcel {parcel.apn}: {e}")
            error_parcels.append(parcel.apn)

    print(f'DONE. Completed {idx - start_idx + 1} parcels. '
          f'Final slope bucket stats={bucket_stats}. '
          f'{len(error_parcels)} failed. Failed parcels:')
    print(error_parcels)


def check_topos_for_parcels(bounding_box: django.contrib.gis.geos.GEOSGeometry):
    """ Check if parcels to be analyzed within bounding box have topography data for them, and create plot to
    visualize """
    parcels = get_parcels_by_neighborhood(bounding_box)
    topo_list = list(TopographyLoads.objects.values_list('extents', flat=True))
    topos = TopographyLoads.objects.all()
    for topo in topos:
        topo_shapely = polygon_to_utm(topo.extents, pyproj.CRS(4326))
        x,y = topo_shapely.exterior.xy
        plt.plot(x,y)
        name = re.sub(r'^Topo_2014_2Ft_(.*).gdb$', r'\1', topo.fname)
        plt.text(topo_shapely.centroid.x-0.01, topo_shapely.centroid.y-0.1, name)

    num_parcels = len(parcels)
    print(f'Checking {num_parcels} parcels...')

    topo_areas = django.contrib.gis.geos.MultiPolygon(topo_list)
    outside_parcels = 0
    for idx, parcel in enumerate(parcels):
        if idx % 5000 == 0:
            print(f"Checking {idx} out of {num_parcels}")
        if not _check_parcel_has_topo(parcel, topo_areas):
            x = parcel.geom.centroid.x
            y = parcel.geom.centroid.y
            plt.plot(x, y, marker="o", markersize=2, markeredgecolor="red", markerfacecolor="yellow")
            outside_parcels += 1
        else:
            x = parcel.geom.centroid.x
            y = parcel.geom.centroid.y
            plt.plot(x, y, marker="o", markersize=1, markeredgecolor="green", markerfacecolor="green")

    print(f'Done. {outside_parcels} found outside the bounds of topo information.')
    print("Close plot to end.")
    plt.show()


def create_slopes_for_parcel(parcel: Parcel, utm_crs: pyproj.CRS, topos_df: geopandas.GeoDataFrame,
                             bucket_stats: Dict):
    """ Create slope polygons and store them in the database for a given parcel. Assumes that topo data is
        present for the parcel.
    """
    # Grade_buckets hold line segments at each grade
    grade_buckets = dict({0: [], 5: [], 10: [], 15: [], 20: [], 25: []})
    parcel_df = models_to_utm_gdf([parcel], utm_crs)

    assert (len(parcel_df.geometry) == 1)
    parcel_poly = parcel_df.geometry[0]
    parcel_df.geometry = parcel_df.geometry.boundary
    utm_crs = parcel_df.estimate_utm_crs()
    p1 = parcel_df.plot()

    # Scan over parcel with horizontal and vertical lines, grabbing intersections with topos. We currently scan
    # horizontally every 1 meter, and vertically every 1 meter.
    for (bucket, line) in _yield_grade_lines(parcel_df, topos_df):
        grade_buckets[bucket].append(line)

    # We have a bunch of lines in grade buckets. Iterate through the buckets, turning lines into
    # polygons (line.buffer(1) to create 1-meter wide polygons), filling holes, and ultimately creating
    # a list of polygons at each grade level that gets saved to the database.
    grade_polys = dict()
    for bucket in [25, 20, 15, 10, 5]:
        throwaways = []
        # Put together all the areas with the given grade into one polygon or multipolygon
        grade_poly = unary_union([line.buffer(1) for line in grade_buckets[bucket]])
        # Clip the poly to the parcel and reduce points by simplifying the poly
        grade_poly = grade_poly.intersection(parcel_poly).simplify(1)
        grade_poly, throwaway_inner = regularize_to_multipolygon(grade_poly)
        throwaways += throwaway_inner
        # Remove polygons from a given grade if we already found a higher grade at that location
        for inner_bkt in range(25, bucket, -5):
            # Ranges: bucket=20 -> inner-bkt=[25]. bucket=0 -> inner-bkt=[25,20,15,10,5]
            grade_poly = grade_poly.difference(grade_polys[inner_bkt])
            # Clean up the resulting geometry into a clean multipolygon
            grade_poly, throwaway_inner = regularize_to_multipolygon(grade_poly)
            throwaways += throwaway_inner

        fill_holes = [Polygon(interior) for interior in yield_interiors(grade_poly) if interior.length < 15]
        grade_poly = unary_union([grade_poly] + fill_holes)
        grade_poly, throwaway_inner = regularize_to_multipolygon(grade_poly)
        throwaways += throwaway_inner

        # Store MultiPolygon into bucket
        grade_polys[bucket] = grade_poly
        if throwaways:
            print("THROWING AWAY", throwaways)
            print("KEEPING", list(grade_poly.geoms))
            bucket_stats['weird'] += 1
        if grade_poly.is_empty:
            bucket_stats['empty'] += 1
        else:
            bucket_stats['full'] += 1

        # Save this slope bucket to the database
        save_slope_object(parcel, bucket, grade_poly, utm_crs)
        # Plot this slope bucket
        if not grade_poly.is_empty:
            geopandas.GeoSeries(grade_poly).plot(ax=p1, color=colors[bucket])
    return p1


def save_slope_object(parcel: Parcel, bucket: int, grade_poly: shapely.geometry, utm_crs: pyproj.CRS):
    # Save the final slope data (a multipolygon) for this bucket.
    # An empty Shapely Multipolygon becomes a GeometryCollection, which doesn't translate
    # properly. So check for emptyness directly instead.
    slope, was_created = ParcelSlope.objects.get_or_create(parcel=parcel, grade=bucket)
    if grade_poly.is_empty:
        slope.polys = django.contrib.gis.geos.MultiPolygon()
    else:
        assert (grade_poly.geom_type == 'MultiPolygon')
        slope.polys = django.contrib.gis.geos.GEOSGeometry(grade_poly.wkt, srid=int(utm_crs.srs.split(':')[1]))
        slope.polys.transform('EPSG:4326')  # in-place conversion to lat-long
    slope.save()


class SortPoint(Point):
    """ Variation of a Shapely Point that is sortable"""

    def __lt__(self, other):
        return True if (self.x < other.x) else (self.x == other.x) and (self.y < other.y)


def get_topo_lines(parcel: Parcel) -> [Topography]:
    """ Get topo lines that intersect with a Django parcel. Returns a Queryset of Topography objects"""
    # Get the topography objects intersecting with a Django parcel instance under consideration. We make the DB
    # calculate the intersection. It's a raw query because Django won't let us overwrite a model field
    # (topography.geom) with a calculated field (the geometry intersection). The query is equivalent to the
    # commented-out normal Django query below.
    topos = Topography.objects.raw(
        'Select id,elev,ltype,index_field,shape_length,ST_Intersection("geom", ST_GeomFromEWKB(%s))::bytea AS "geom" '
        'from world_topography WHERE ST_Intersects("geom", ST_GeomFromEWKB(%s))',
        [parcel.geom.buffer(0.00005).ewkb, parcel.geom.buffer(0.00005).ewkb]
    )
    # topos = Topography.objects.filter(    # this is the query we want, but Django won't let us do.
    #     geom__intersects=parcel.geom).annotate(geom=Intersection('geom', parcel.geom)).defer('geom')
    return topos


# yield tuple for each point in a list consisting of (Point, elevation, index (for debugging))
# Note that we yield SortPoint objects, which is important so the caller can sort them.
def _yield_pts(intersect, topos_df):
    for index, pt in enumerate(intersect):
        if pt.is_empty: continue
        if (pt.geom_type == 'MultiPoint'):
            for inner_pt in pt.geoms:
                yield (SortPoint(inner_pt), topos_df['elev'][index], index)
        else:
            yield (SortPoint(pt), topos_df['elev'][index], index)


def _yield_grade_lines_from_intersections(intersections, topos_df):
    # take a series of intersection points with the topography in topos_df, and yield individual
    # grades (aka slopes) and lines
    intersect_tuples = sorted(_yield_pts(intersections, topos_df))
    for i in range(len(intersect_tuples) - 1):
        pt0 = intersect_tuples[i][0]
        pt1 = intersect_tuples[i + 1][0]
        run = pt0.distance(pt1) * 3.28  # convert meters to feet
        rise = intersect_tuples[i + 1][1] - intersect_tuples[i][1]  # already in feet
        if rise == 0 or run == 0: continue
        grade_percent = abs(round(rise / run * 100, 1))
        grade_bucket = int(grade_percent / 5) * 5  # grade_bucket should be 0 if grade_percent < 5
        if grade_bucket > 25:
            grade_bucket = 25  # biggest grade_bucket is 25, so clamp results to that.
        yield grade_bucket, LineString([pt0, pt1])


def _yield_grade_lines(parcel_df, topos_df):
    # For a parcel and related topo, yield individual grades and lines as tuples (grade bucket, line)
    (xmin, ymin, xmax, ymax) = parcel_df.total_bounds.round().astype(int).tolist()

    # Do a horizontal scan
    for y in range(ymin, ymax):
        intersect = topos_df.geometry.intersection(LineString([(xmin, y), (xmax, y)]))
        yield from _yield_grade_lines_from_intersections(intersect, topos_df)

    # Do a vertical scan
    for x in range(xmin, xmax):
        intersect = topos_df.geometry.intersection(LineString([(x, ymin), (x, ymax)]))
        yield from _yield_grade_lines_from_intersections(intersect, topos_df)


def _check_parcel_has_topo(parcel: Parcel, topo_areas: django.contrib.gis.geos.MultiPolygon):
    if any([parcel.geom.within(x) for x in topo_areas]):
        return True
    else:
        print("Parcel at location", parcel.geom.centroid, " not represented in Topo Areas!")
        return False
