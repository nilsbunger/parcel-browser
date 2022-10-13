import django

django.setup()


def parallel_analyze_road_worker(*args, **kwargs):
    from lib.analyze_road_lib import analyze_road_worker

    analyze_road_worker(*args, **kwargs)
