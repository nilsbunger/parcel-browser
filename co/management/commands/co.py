from collections import Counter
from enum import Enum
import logging
import pprint
import statistics
import sys
from time import perf_counter

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Polygon
from django.core.management import BaseCommand
import geopandas
from geopandas import GeoSeries, GeoDataFrame
import matplotlib.pyplot as plt
import shapely
from shapely.geometry import LineString

from lib import mgmt_cmd_lib
from lib.crs_lib import get_utm_crs, meters_to_latlong
from lib.parcel_lib import models_to_utm_gdf, normalize_geometries
from world.models import Parcel, Roads
from world.models.models import AnalyzedRoad


class CoCmd(Enum):
    eligible = 1


def get_nearby_parcels_and_roads_df(model_obj, distance, crs):
    """Return dataframes of nearby parcels and roads within a distance (in meters) of a Django model object w/ a geom field."""

    # for fast (not 100% accurate) distance calculations, keep calculation in degrees.
    # Lat and long delta aren't necessarily the same, so we use the average of them.
    (lat_delta, long_delta) = meters_to_latlong(
        distance, baselat=model_obj.geom.centroid.y, baselong=model_obj.geom.centroid.x
    )
    starttime = perf_counter()
    #    bbox = Polygon.from_bbox([*model_obj.geom.boundary[0], *model_obj.geom.boundary[1]])
    near_parcels = (
        Parcel.objects.using("basedata")
        # .filter(geom__bboverlaps=bbox)
        .filter(geom__dwithin=(model_obj.geom.centroid, (lat_delta + long_delta) / 2 * 2))
        .annotate(distance=Distance("geom", model_obj.geom))
        .order_by("distance")
    )
    near_parcels_df = models_to_utm_gdf(near_parcels, crs, fields=["apn", "address", "geom"])
    elapsed = perf_counter() - starttime
    sys.stderr.write(f"\nPARCELS Elapsed time: {elapsed} seconds\n")
    roads = (
        Roads.objects.using("basedata")
        .filter(geom__dwithin=(model_obj.geom, (lat_delta + long_delta) / 2))
        .annotate(dis=Distance("geom", model_obj.geom))
        .order_by("dis")
    )
    roads_df = models_to_utm_gdf(
        roads,
        crs,
        fields=["distance", "rd30full", "length", "rightway", "id", "geom"],
    )
    model_obj_df = models_to_utm_gdf([model_obj], crs)
    model_obj_xlat, [roads_xlat, near_parcels_xlat] = normalize_geometries(
        model_obj_df, [roads_df, near_parcels_df]
    )

    return model_obj_xlat, roads_xlat, near_parcels_xlat
    # # near_parcels_xlat = near_parcels_df
    # # roads_xlat = roads_df
    # return near_parcels_xlat, roads_xlat


class Command(BaseCommand):
    help = "Add help text here..."

    def add_arguments(self, parser):
        parser.add_argument("cmd", choices=CoCmd.__members__)
        parser.add_argument("rest", action="store", nargs="*")
        parser.add_argument("--xoxo", action="store_true", help="kiss")
        mgmt_cmd_lib.add_common_arguments(parser)

    def evaluate_ab2011_from_roads(self):
        sd_utm_crs = get_utm_crs()
        # TODO: We don't clean up ANalyzedRoad entries that should be excluded. Maybe we should list *all* roads in
        #  AnalyzedRoads, even ones we aren't analyzing. If we do that we need to index on exclusion criteria.
        roads_qs = (
            Roads.objects.filter(lpsjur="SD").exclude(funclass__in=["1", "A", "B", "F", "W"]).order_by("roadsegid")
        )
        start_idx = 23923 + 13743  # TODO: REMOVE INDEX
        stats = Counter({})
        stats["exception_list"] = []
        plot = False
        logging.info(f"Evaluating {roads_qs.count()} roads")
        for idx, road_under_test in enumerate(roads_qs[start_idx:]):
            try:
                analyzed_road = AnalyzedRoad(road=road_under_test)
                if plot:
                    plt.close()
                    fig = plt.figure("HI")
                    ax = fig.add_subplot()
                # Get nearby parcels and roads as GeoDataFrames, and normalize them all to 0,0 base
                if road_under_test.length < 20:  #  django object length is in feet
                    analyzed_road.status = AnalyzedRoad.Status.TOO_SHORT
                    analyzed_road.save()
                    stats["skip:too_short"] += 1
                    continue
                subsegs = [0.45]
                if road_under_test.length > 100:  # django object length is in feet
                    subsegs.extend([0.35, 0.55])
                if road_under_test.length > 200:  # django object length is in feet
                    subsegs.extend([0.65, 0.25])
                if road_under_test.length > 400:  # django object length is in feet
                    subsegs.extend([0.75, 0.15])
                road_under_test_df, roads_df, parcels_df = get_nearby_parcels_and_roads_df(
                    road_under_test, distance=100, crs=sd_utm_crs
                )
                # Plot background items
                logging.info(
                    f"Calculating idx={idx} road roadsegid={road_under_test.roadsegid} : {road_under_test.abloaddr}-{road_under_test.abhiaddr} {road_under_test.rd30full}"
                    f". Length={round(road_under_test_df.length.values[0],1)} meters"
                )
                parcels_blob_df = parcels_df.dissolve()
                if plot:
                    bounds = road_under_test_df.bounds
                    plt.ylim([float(bounds.miny) - 100, float(bounds.maxy) + 100])
                    plt.xlim([float(bounds.minx) - 100, float(bounds.maxx) + 100])
                    parcels_df.plot(ax=ax, color="gray")
                    roads_df.plot(ax=ax, color="orange")
                    try:
                        road_under_test_df.boundary.plot(ax=ax, color="blue")
                    except:
                        # Some weird cases, like a segment that circles back on itself, have no boundary
                        logging.info("Couldn't plot road boundary")
                    road_under_test_df.plot(ax=ax, color="red")
                road_widths = []
                # CHeck if segment is in any parcel. if any result of the join is not NAN, then it's in a parcel
                if (
                    road_under_test_df.sjoin(
                        parcels_df,
                        how="left",
                    )
                    .model_right.notna()
                    .any()
                ):
                    logging.info(f"Road segment is inside a parcel. Skipping")
                    stats["skip:inside_parcel"] += 1
                    analyzed_road.status = AnalyzedRoad.Status.INSIDE_PARCEL
                    analyzed_road.save()
                    if plot:
                        plt.show()
                    continue
                if road_under_test_df.intersects(parcels_blob_df).values[0]:
                    logging.info("  Road segment crosses a parcel boundary - skipping")
                    stats["skip:crosses_parcel"] += 1
                    analyzed_road.status = AnalyzedRoad.Status.CROSSES_PARCEL
                    analyzed_road.save()
                    if plot:
                        plt.show()
                    continue
                # Get the road width at multiple points (subsegments).
                for subsegment in subsegs:
                    start_pt = road_under_test_df.interpolate(subsegment, normalized=True).values[0]
                    end_pt = road_under_test_df.interpolate(subsegment + 0.1, normalized=True).values[0]
                    mid_line = LineString([start_pt, end_pt])
                    midpoint = mid_line.centroid
                    dx = end_pt.x - start_pt.x
                    dy = end_pt.y - start_pt.y
                    normal_line = LineString(
                        [[-dy + midpoint.x, dx + midpoint.y], [dy + midpoint.x, -dx + midpoint.y]]
                    )
                    scale_fact = 200 / normal_line.length
                    normal_line = shapely.affinity.scale(normal_line, xfact=scale_fact, yfact=scale_fact)
                    clipped_line_df = geopandas.overlay(
                        GeoDataFrame(geometry=GeoSeries(normal_line), crs=sd_utm_crs),
                        parcels_blob_df,
                        how="difference",
                    )
                    clipped_line_df = clipped_line_df.explode(index_parts=False)
                    # There can be more than one clipped line segment, so find the one that crosses the segment being tested
                    normal_segment = clipped_line_df[clipped_line_df.intersects(mid_line)]
                    # Check that the normal didn't extend out past other roads... if it did, throw it out
                    crossed_roads = normal_segment.sjoin(roads_df, how="left")
                    if len(crossed_roads) > 1:
                        print("  Normal segment crosses more than one road - skipping segment")
                        stats["skip_subseg:crosses_more_than_one_road"] += 1
                        road_widths.append(-1)
                    elif len(normal_segment) == 0:
                        print("  Normal segment is empty - skipping segment")
                        stats["skip_subseg:empty"] += 1
                        road_widths.append(-2)
                    else:
                        seg_length = round(normal_segment.length.values[0], 2)
                        if seg_length > 150:
                            print("  Road width is too large - skipping segment")
                            stats["skip_subseg:width_too_large"] += 1
                            road_widths.append(-3)
                        else:
                            stats["ok_subseg"] += 1
                            road_widths.append(seg_length)
                    if plot:
                        # GeoSeries(mid_line).plot(ax=ax, color="blue")
                        GeoSeries(normal_line).plot(ax=ax, color="blue")
                        normal_segment.plot(ax=ax, color="green")
                logging.info(f"  Road widths: {road_widths}")
                # calculate road width stats
                if plot:
                    plt.show()
                    pass

                analyzed_road.all_widths = road_widths
                good_widths = [x for x in road_widths if x >= 0]
                good_widths.sort()
                if len(good_widths) == 0:
                    logging.info(f"  No good road widths found - skipping road")
                    stats["skip:no_good_widths"] += 1
                    analyzed_road.status = AnalyzedRoad.Status.NO_WIDTHS
                    analyzed_road.save()
                else:
                    if len(good_widths) > 4:
                        # with at least 5 entries, throw away largest and smallest
                        good_widths = good_widths[1:-1]
                    analyzed_road.avg_width = round(statistics.mean(good_widths), 2)
                    analyzed_road.stdev_width = round(statistics.pstdev(good_widths, analyzed_road.avg_width), 2)
                    if analyzed_road.stdev_width / analyzed_road.avg_width > 0.1:
                        stats["skip:width_too_unstable"] += 1
                        logging.info(f"  Road width stdev is too large - skipping road")
                        analyzed_road.status = AnalyzedRoad.Status.UNSTABLE_WIDTHS
                        analyzed_road.save()
                        continue
                    analyzed_road.low_width = good_widths[0]
                    analyzed_road.high_width = good_widths[-1]
                    analyzed_road.save()
                    stats["ok"] += 1
            except Exception as e:
                analyzed_road.status = AnalyzedRoad.Status.EXCEPTION
                analyzed_road.save()
                logging.exception(f"Error processing road {road_under_test}")
                stats["exception"] += 1
                stats["exception_list"].append(road_under_test.roadsegid)
        logging.info(f"DONE. Stats:{stats}")

    def evaluate_road_width_from_parcel(self):
        """First attempt at cehcking a parcel for AB2011 "commercial corridor" 75-150ft width test"""

        # Start from a specific parcel, and evaluate it.
        apn = "3615922000"  # 5145 CLAIREMONT MESA BLVD, commercial parcel
        sd_utm_crs = get_utm_crs()

        # Roads table says width of Clairemont Mesa Blvd is 102 ft
        main_parcel = Parcel.objects.using("basedata").get(apn=apn)
        main_parcel_df = models_to_utm_gdf([main_parcel], sd_utm_crs, fields=["apn", "address", "geom"])
        roads_df, parcels_df = get_nearby_parcels_and_roads_df(main_parcel, distance=100, crs=sd_utm_crs)

        for idx, row in roads_df.iterrows():
            sys.stderr.write(f"{row['rd30full']} {row['length']}, dist={roads[idx].distance}\n")
            points = nearest_points(row["geometry"], parcel_df["geometry"][0])
            ### UPDATE THIS: ANGLE needs to be angle of ROAD relative to angle of
            ### this line... we want lines that are perpendicular to the road

            assert False
            angle = arctan2(points[1].y - points[0].y, points[1].x - points[0].x)
            angle = abs(degrees(angle))
            sys.stderr.write(f"angle={angle}\n")
            if idx == 0:
                near_lines.append(LineString([points[0], points[1]]))
            sys.stderr.write(f"{points}")

        fig = plt.figure(parcel.address)
        ax = fig.add_subplot()
        plt.title(parcel.apn + ":" + parcel.address)
        roads_xlat.plot(ax=ax, color="red")
        near_parcels_xlat.plot(ax=ax, color="gray")
        parcel_xlat.plot(ax=ax, color="blue")
        _, near_lines_xlat = normalize_geometries(parcel_df, GeoSeries(near_lines))
        near_lines_xlat.plot(ax=ax, color="cyan")
        plt.ylim([-100, 100])
        plt.xlim([-100, 100])
        plt.show()

    def handle(self, cmd, rest, *args, **options):
        mgmt_cmd_lib.init(verbose=options["verbose"])
        logging.info(f"Running cmd = {cmd}, rest={rest}, options:\n{pprint.pformat(options)}")
        assert cmd == "eligible"
        # self.evaluate_road_width_from_parcel()
        self.evaluate_ab2011_from_roads()
