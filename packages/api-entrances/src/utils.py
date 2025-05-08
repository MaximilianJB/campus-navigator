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
        
        # Try different possible property names for the polygon name
        properties = poly_feature.get("properties", {})
        
        # Check various possible name properties in order of preference
        name_properties = ["name", "Name", "NAME"]
        poly_name = None
        
        # First check standard name properties
        for prop in name_properties:
            if prop in properties and properties[prop]:
                poly_name = properties[prop]
                break
                
        # If no name found, check the 'name:' property which appears in this GeoJSON file
        if not poly_name and "name:" in properties and properties["name:"]:
            poly_name = properties["name:"]
            print(f"Found name in 'name:' property: {poly_name}")
        
        # If no name was found, generate a default name using the index
        if not poly_name:
            poly_name = f"Building_{len(labeled_entrances) + 1}"
            print(f"Warning: No name found for polygon. Using '{poly_name}' instead.")
            print(f"Available properties: {list(properties.keys())}")
            
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
