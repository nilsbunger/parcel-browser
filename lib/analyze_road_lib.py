from joblib import Parallel, delayed
import pyproj

from lib.parallel_worker import parallel_analyze_road_worker
from world.models import Roads


def analyze_road_batch(
    roads: list[Roads],
    utm_crs: pyproj.CRS,
    single_process=False,
):
    n_jobs = 1 if single_process else 2
    if n_jobs == 1:
        results = [analyze_road_worker(road, utm_crs) for road in roads]
    else:
        results = Parallel(n_jobs=n_jobs)(
            delayed(parallel_analyze_road_worker)(road, utm_crs) for road in roads
        )


def analyze_road_worker(road: Roads, utm_crs: pyproj.CRS):
    # print(f"Analyzing road {road.name}")
    road.analyze(utm_crs)
    assert False, "Not implemented yet... copy from co.py mgmt command"
    return road
