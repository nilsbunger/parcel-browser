""" Methods for manipulating Shapely objects (no dependencies on Django / etc)"""

from shapely.geometry import MultiPolygon, MultiLineString
from shapely.ops import split
from lib.types import Polygonal


def regularize_to_multipolygon(grade_poly):
    # Throwaway non-polygons in a shapely geom. Returns MultiPolygon and 'throwaway' list as a tuple
    if grade_poly.is_empty:
        return MultiPolygon(), []
    elif grade_poly.geom_type == "Polygon":
        grade_poly = MultiPolygon([grade_poly])
        assert grade_poly.geom_type == "MultiPolygon"
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
    """Accepts a shapely polygon or collection (MultiPolygon or GeometryCollection).
    Yields polygon "interiors"", meaning 'holes' inside the polygon"""
    # takes a polygon or multipolygon and yields its interiors
    if poly.geom_type == "MultiPolygon":
        for geom in poly.geoms:
            for interior in geom.interiors:
                yield interior
    elif poly.geom_type == "GeometryCollection":
        for geom in poly.geoms:
            if geom.geom_type in ["LineString", "MultiLineString"]:
                # skip line strings... not sure why they are in here... debug later!
                continue
            for interior in geom.interiors:
                yield interior
    else:
        if poly.geom_type in ["LineString", "MultiLineString"]:
            return
        for interior in poly.interiors:
            yield interior


def multi_line_string_split(poly: Polygonal, multiline: MultiLineString) -> list[Polygonal]:
    """Splits a polygon by using a MultiLineString into multiple parts.

    Args:
        poly (Polygonal): The polyogn to split
        multiline (MultiLineString): The line to split the polygon

    Returns:
        list[Polygonal]: A list of polygonal objects after split
    """
    completed = []
    if isinstance(poly, MultiPolygon):
        unsplit = list(poly.geoms)
    else:
        unsplit = [poly]

    # Now we keep splitting polygons in unsplit until they don't have
    # our multiline running through them
    while unsplit:
        poly_to_split = unsplit.pop()

        # Now try splitting the poly with each line of the multiline
        for line in multiline.geoms:
            split_geom = split(poly_to_split, line)
            if len(split_geom.geoms) > 1:
                unsplit.extend([g for g in split_geom.geoms if g.area > 0.01])
                break
        else:
            completed.append(poly_to_split)

    return completed
