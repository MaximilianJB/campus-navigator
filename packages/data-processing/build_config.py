import json
import geojson
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
from shapely.ops import nearest_points
import os
import argparse
import sys

# Constants
GRID_SPACING = 0.00002  # ~2 meters, matches vector_pathfinding.py
BUILDING_PADDING = 1.0  # ~2 meters
HALLWAY_RADIUS = 0.75  # Matches vector_pathfinding.py

# Helper functions from vector_pathfinding.py
def rasterize_line(grid, minx, miny, grid_spacing, line, width=1, value=0):
    height, width_grid = grid.shape
    # Cast width to integer to avoid TypeError in range
    width = int(round(width))
    if line.length == 0:
        x, y = line.xy[0][0], line.xy[1][0]
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    grid[iiy, iix] = value
        return
    num_points = int(line.length / grid_spacing) + 1
    if num_points == 1:
        x, y = line.xy[0][0], line.xy[1][0]
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    grid[iiy, iix] = value
        return
    for i in range(num_points):
        pt = line.interpolate(i * line.length / (num_points - 1))
        x, y = pt.x, pt.y
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    grid[iiy, iix] = value

def find_building_for_entrance(entrance, buildings):
    for b in buildings:
        if b.contains(entrance) or b.exterior.distance(entrance) < 1e-9:
            return b
    return None

def rasterize_map(bounds_poly, buildings, hallways, entrances, grid_spacing, building_padding=1.0, hallway_radius=0.75):
    minx, miny, maxx, maxy = bounds_poly.bounds
    width = int(np.ceil((maxx - minx) / grid_spacing))
    height = int(np.ceil((maxy - miny) / grid_spacing))
    grid = np.zeros((height, width), dtype=np.uint8)  # 0 = walkable, 1 = obstacle

    # Rasterize buildings first
    padded_buildings = [b.buffer(building_padding * grid_spacing) for b in buildings]
    building_tree = STRtree(padded_buildings)
    building_cell_counts = []
    for b in padded_buildings:
        count = 0
        minx_b, miny_b, maxx_b, maxy_b = b.bounds
        min_ix = max(0, int((minx_b - minx) / grid_spacing))
        max_ix = min(width, int((maxx_b - minx) / grid_spacing) + 1)
        min_iy = max(0, int((miny_b - miny) / grid_spacing))
        max_iy = min(height, int((maxy_b - miny) / grid_spacing) + 1)
        for iy in range(min_iy, max_iy):
            for ix in range(min_ix, max_ix):
                x = minx + ix * grid_spacing + grid_spacing / 2
                y = miny + iy * grid_spacing + grid_spacing / 2
                pt = Point(x, y)
                if b.contains(pt):
                    grid[iy, ix] = 1
                    count += 1
        building_cell_counts.append(count)
    print(f"Building cell counts: {building_cell_counts}")
    print(f"Total obstacle cells: {np.sum(grid == 1)}")

    # Rasterize hallways and entrances after buildings to override obstacles
    for hallway in hallways:
        rasterize_line(grid, minx, miny, grid_spacing, hallway, width=hallway_radius, value=0)

    for entrance in entrances:
        building = find_building_for_entrance(entrance, buildings)
        if building is None:
            continue
        building_hallways = [h for h in hallways if h.intersects(building)]
        if building_hallways:
            nearest_hallway = min(building_hallways, key=lambda h: h.distance(entrance))
            nearest_point_on_hallway = nearest_points(entrance, nearest_hallway)[1]
            connection = LineString([entrance, nearest_point_on_hallway])
            rasterize_line(grid, minx, miny, grid_spacing, connection, width=hallway_radius, value=0)
        if building.contains(entrance):
            exterior_point = nearest_points(entrance, building.exterior)[1]
            connection_to_outside = LineString([entrance, exterior_point])
            rasterize_line(grid, minx, miny, grid_spacing, connection_to_outside, width=hallway_radius, value=0)
        x, y = entrance.x, entrance.y
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        if 0 <= ix < width and 0 <= iy < height:
            grid[iy, ix] = 0

    return grid, minx, miny, grid_spacing

if __name__ == "__main__":
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Build grid configuration from GeoJSON")
    # Robust path to default GeoJSON
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_GEOJSON_PATH = os.path.join(SCRIPT_DIR, "Full.geojson")
    parser.add_argument('--input', type=str, default=DEFAULT_GEOJSON_PATH,
                        help='Path to input GeoJSON file')
    parser.add_argument('--output', type=str, default=os.path.join(SCRIPT_DIR, "grid_config.json"),
                        help='Path to output JSON file')
    args = parser.parse_args()

    # Input and output file paths
    input_geojson_path = args.input
    output_json_path = args.output

    # Load GeoJSON
    if not os.path.exists(input_geojson_path):
        print(f"Error: GeoJSON file not found: {input_geojson_path}")
        sys.exit(1)

    with open(input_geojson_path, "r") as f:
        gj = geojson.load(f)

    # Parse GeoJSON features
    buildings = []
    building_labels = []
    hallways = []
    entrances = []
    bounds_poly = None

    for feat in gj["features"]:
        geom_type = feat["geometry"]["type"]
        props = feat.get("properties", {})
        if geom_type == "Polygon":
            if props.get("name") == "Bounds":
                bounds_poly = Polygon(feat["geometry"]["coordinates"][0])
            else:
                poly = Polygon(feat["geometry"]["coordinates"][0])
                buildings.append(poly)
                building_labels.append(props.get("name", ""))
        elif geom_type == "LineString":
            hallways.append(LineString(feat["geometry"]["coordinates"]))
        elif geom_type == "Point":
            entrances.append(Point(feat["geometry"]["coordinates"]))

    if bounds_poly is None:
        print("Error: No 'Bounds' polygon found in GeoJSON")
        sys.exit(1)

    print(f"Loaded {len(buildings)} buildings, {len(hallways)} hallways, {len(entrances)} entrances.")

    # Rasterize the map
    grid, minx, miny, grid_spacing = rasterize_map(
        bounds_poly, buildings, hallways, entrances, GRID_SPACING, BUILDING_PADDING, HALLWAY_RADIUS
    )

    # Convert numpy array to list for JSON serialization
    grid_list = grid.tolist()

    # Create output JSON
    output_json = {
        "rows": grid.shape[0],
        "cols": grid.shape[1],
        "lat_min": miny,
        "lat_max": miny + grid.shape[0] * grid_spacing,
        "lng_min": minx,
        "lng_max": minx + grid.shape[1] * grid_spacing,
        "grid": grid_list
    }

    # Write to file
    with open(output_json_path, 'w') as file:
        json.dump(output_json, file, indent=2)

    print(f"Grid configuration saved to {output_json_path}")
    print(f"Grid shape: {grid.shape[0]}x{grid.shape[1]}")
    print(f"Walkable cells: {np.sum(grid == 0)}")
    print(f"Obstacle cells: {np.sum(grid == 1)}")