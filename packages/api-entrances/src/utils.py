"""
Utility functions for GeoJSON processing
"""
import math
import json
from shapely.geometry import Point, shape

def angle_from_north(center, point):
    """Calculate the angle from north in degrees."""
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    angle = math.degrees(math.atan2(dx, dy))  # Swap dx/dy to start from north
    return (angle + 360) % 360  # Normalize to [0, 360)

def process_geojson_entrances(geojson_data):
    """Process GeoJSON data to label entrance points in clockwise order.
    
    Args:
        geojson_data (dict): Parsed GeoJSON data containing polygons and points
        
    Returns:
        list: List of dictionaries containing labeled entrance points
    """
    polygons = []
    points = []
    labeled_entrances = []

    for feature in geojson_data["features"]:
        if feature["geometry"]["type"] == "Polygon":
            polygons.append(feature)
        elif feature["geometry"]["type"] == "Point":
            points.append(feature)

    # Sort polygons by area, smallest first
    polygons.sort(key=lambda f: shape(f["geometry"]).area)

    assigned_points = set()

    for poly_feature in polygons:
        poly_geom = shape(poly_feature["geometry"])
        poly_name = poly_feature["properties"].get("name")
        centroid = poly_geom.centroid.coords[0]

        contained_points = []
        for i, point_feature in enumerate(points):
            if i in assigned_points:
                continue  # Skip already labeled points

            coords = point_feature["geometry"]["coordinates"]
            point_geom = Point(coords)

            if poly_geom.contains(point_geom):
                angle = angle_from_north(centroid, coords)
                contained_points.append((angle, coords, i))

        # Sort clockwise from north
        contained_points.sort()

        # Label and store in list
        for j, (_, coords, original_index) in enumerate(contained_points, start=1):
            assigned_points.add(original_index)
            point_name = f"{poly_name}_{j:02}"
            labeled_entrances.append({
                "label": point_name,
                "latitude": coords[1],
                "longitude": coords[0]
            })

    return labeled_entrances
