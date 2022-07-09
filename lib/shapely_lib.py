""" Methods for manipulating Shapely objects (no dependencies on Django / etc)"""

from shapely.geometry import MultiPolygon


def regularize_to_multipolygon(grade_poly):
    # Throwaway non-polygons in a shapely geom. Returns MultiPolygon and 'throwaway' list as a tuple
    if grade_poly.is_empty:
        return MultiPolygon(), []
    elif grade_poly.geom_type == "Polygon":
        grade_poly = MultiPolygon([grade_poly])
        assert (grade_poly.geom_type == 'MultiPolygon')
        return grade_poly, []
    elif grade_poly.geom_type == "LineString":
        throwaways = [grade_poly]
        grade_poly = MultiPolygon([])
        return grade_poly, throwaways
    else:
        throwaways = [poly for poly in grade_poly.geoms if poly.geom_type != "Polygon"]
        grade_poly = MultiPolygon([poly for poly in grade_poly.geoms if poly.geom_type == "Polygon"])
        return grade_poly, throwaways


def yield_interiors(poly):
    """ Accepts a shapely polygon or collection (MultiPolygon or GeometryCollection).
        Yields polygon "interiors"", meaning 'holes' inside the polygon """
    # takes a polygon or multipolygon and yields its interiors
    if poly.geom_type == 'MultiPolygon':
        for geom in poly.geoms:
            for interior in geom.interiors:
                yield interior
    elif poly.geom_type == 'GeometryCollection':
        for geom in poly.geoms:
            if geom.geom_type in ['LineString', 'MultiLineString']:
                # skip line strings... not sure why they are in here... debug later!
                continue
            for interior in geom.interiors:
                yield interior
    else:
        if poly.geom_type in ['LineString', 'MultiLineString']:
            return
        for interior in poly.interiors:
            yield interior
