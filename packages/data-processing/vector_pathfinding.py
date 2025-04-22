import geojson
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
from shapely.ops import nearest_points
import os
import sys
from collections import deque

# --- Add pathfinding-core to sys.path ---
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'pathfinding-core'))

from a_star import AStar, get_neighbors

# --- Robust path to GeoJSON ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(SCRIPT_DIR, "Full.geojson")
PATH_EXPORT = os.path.join(SCRIPT_DIR, "path.geojson")
GRID_SPACING = 0.00002  # ~2m
BUILDING_PADDING = 1.0  # ~2m

# --- Load GeoJSON ---
with open(GEOJSON_PATH, "r") as f:
    gj = geojson.load(f)

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

print(f"Loaded {len(buildings)} buildings, {len(hallways)} hallways, {len(entrances)} entrances.")

# --- Helper functions ---
def get_geoms_from_query(query_result, geom_list):
    for obj in query_result:
        if hasattr(obj, "contains"):
            yield obj
        elif isinstance(obj, (int, np.integer)):
            yield geom_list[obj]

def find_building_for_entrance(entrance, buildings):
    for b in buildings:
        if b.contains(entrance) or b.exterior.distance(entrance) < 1e-9:
            return b
    return None

def rasterize_line(grid, minx, miny, grid_spacing, line, width=1, value=0):
    height, width_grid = grid.shape
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

def rasterize_map(bounds_poly, buildings, hallways, entrances, grid_spacing, building_padding=1.0, hallway_radius=.75):
    minx, miny, maxx, maxy = bounds_poly.bounds
    width = int(np.ceil((maxx - minx) / grid_spacing))
    height = int(np.ceil((maxy - miny) / grid_spacing))
    grid = np.zeros((height, width), dtype=np.uint8)  # 0 = walkable
    hallway_grid = np.ones((height, width), dtype=float)  # Cost grid

    # Rasterize buildings
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

    # Rasterize hallways and entrances
    for hallway in hallways:
        rasterize_line(grid, minx, miny, grid_spacing, hallway, width=hallway_radius, value=0)
        rasterize_line(hallway_grid, minx, miny, grid_spacing, hallway, width=hallway_radius, value=0.1)

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
            rasterize_line(hallway_grid, minx, miny, grid_spacing, connection, width=hallway_radius, value=0.1)
        if building.contains(entrance):
            exterior_point = nearest_points(entrance, building.exterior)[1]
            connection_to_outside = LineString([entrance, exterior_point])
            rasterize_line(grid, minx, miny, grid_spacing, connection_to_outside, width=hallway_radius, value=0)
            rasterize_line(hallway_grid, minx, miny, grid_spacing, connection_to_outside, width=hallway_radius, value=0.1)
        x, y = entrance.x, entrance.y
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        if 0 <= ix < width and 0 <= iy < height:
            grid[iy, ix] = 0
            hallway_grid[iy, ix] = 0.1

    return grid, hallway_grid, minx, miny, grid_spacing

def world_to_grid(x, y, minx, miny, grid_spacing):
    ix = int((x - minx) / grid_spacing)
    iy = int((y - miny) / grid_spacing)
    ix = max(0, min(ix, grid.shape[1] - 1))
    iy = max(0, min(iy, grid.shape[0] - 1))
    return ix, iy

def grid_to_world(ix, iy, minx, miny, grid_spacing):
    x = minx + ix * grid_spacing + grid_spacing / 2
    y = miny + iy * grid_spacing + grid_spacing / 2
    return x, y

def snap_to_walkable(ix, iy, grid):
    if 0 <= iy < grid.shape[0] and 0 <= ix < grid.shape[1] and grid[iy, ix] == 0:
        return ix, iy
    for di in range(-10, 11):
        for dj in range(-10, 11):
            ni, nj = iy + di, ix + dj
            if 0 <= ni < grid.shape[0] and 0 <= nj < grid.shape[1] and grid[ni, nj] == 0:
                return nj, ni
    print(f"No walkable cells near ({ix}, {iy}). Grid values (5x5):")
    for dy in range(-2, 3):
        row = [grid[iy + dy, ix + dx] if 0 <= iy + dy < grid.shape[0] and 0 <= ix + dx < grid.shape[1] else 'X' for dx in range(-2, 3)]
        print(row)
    return None

def flood_fill(grid, start):
    if grid[start[1], start[0]] == 1:
        return set()
    height, width = grid.shape
    reachable = set()
    queue = deque([start])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while queue:
        x, y = queue.popleft()
        if (x, y) in reachable:
            continue
        reachable.add((x, y))
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= ny < height and 0 <= nx < width and grid[ny, nx] != 1 and (nx, ny) not in reachable:
                queue.append((nx, ny))
    return reachable

# --- Rasterize the map ---
grid, hallway_grid, minx, miny, grid_spacing = rasterize_map(bounds_poly, buildings, hallways, entrances, GRID_SPACING, BUILDING_PADDING, hallway_radius=3)
print(f"Rasterized grid shape: {grid.shape}")

# --- Debug grid ---
walkable_cells = np.sum(grid == 0)
obstacle_cells = np.sum(grid == 1)
hallway_cells = np.sum(hallway_grid == 0.1)
print(f"Grid stats: {walkable_cells} walkable cells, {obstacle_cells} obstacle cells")
print(f"Hallway cells (cost 0.1): {hallway_cells}")

# --- Plot Map ---
fig, ax = plt.subplots(figsize=(12, 8))
for h in hallways:
    x, y = h.xy
    ax.plot(x, y, color="gray", linewidth=2, alpha=0.7, zorder=1, label="Hallway" if 'Hallway' not in ax.get_legend_handles_labels()[1] else None)
for i, b in enumerate(buildings):
    x, y = b.exterior.xy
    ax.fill(x, y, color="#3388ff", alpha=0.5)
    label = building_labels[i]
    if label:
        cx, cy = b.centroid.x, b.centroid.y
        ax.text(cx, cy, label, fontsize=4, ha='center', va='center', color='black',
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.2'))
for e in entrances:
    x, y = e.xy
    ax.plot(x, y, "ro", markersize=5)
if bounds_poly is not None:
    x, y = bounds_poly.exterior.xy
    ax.plot(x, y, color="black", linestyle="--", linewidth=1, label="Bounds")

plt.title("Campus Map (click start and end points)")
plt.tight_layout()
plt.show(block=False)

# --- User selects start and end ---
print("Click on the map to select START and END points, then close the window.")
clicked = plt.ginput(2, timeout=-1)
plt.close()

start_world = clicked[0]
goal_world = clicked[1]

start_grid = world_to_grid(start_world[0], start_world[1], minx, miny, grid_spacing)
goal_grid = world_to_grid(goal_world[0], goal_world[1], minx, miny, grid_spacing)

# --- Debug grid visualization ---
plt.imshow(grid, cmap='binary', origin='upper')
plt.plot([start_grid[0]], [start_grid[1]], 'ro', label='Start')
plt.plot([goal_grid[0]], [goal_grid[1]], 'bo', label='Goal')
plt.legend()
plt.title("Grid (White=Walkable, Black=Obstacle)")
plt.show(block=False)
plt.pause(2)
plt.close()

start_grid = snap_to_walkable(start_grid[0], start_grid[1], grid)
goal_grid = snap_to_walkable(goal_grid[0], goal_grid[1], grid)

if start_grid is None or goal_grid is None:
    print("Start or goal point cannot be snapped to a walkable area!")
    print(f"Original start grid: {world_to_grid(start_world[0], start_world[1], minx, miny, grid_spacing)}")
    print(f"Original goal grid: {world_to_grid(goal_world[0], goal_world[1], minx, miny, grid_spacing)}")
    path_world = []
else:
    print(f"Snapped start: {start_grid}, goal: {goal_grid}")
    print(f"Start grid value: {grid[start_grid[1], start_grid[0]]}")
    print(f"Goal grid value: {grid[goal_grid[1], goal_grid[0]]}")

    # --- Check connectivity with flood fill ---
    reachable = flood_fill(grid, start_grid)
    if tuple(goal_grid) in reachable:
        print("Start and goal are in the same walkable region.")
    else:
        print("Start and goal are in different walkable regions!")

import numpy as np
import matplotlib.pyplot as plt

# --- Run grid-based A* pathfinding ---
astar = AStar(grid, hallway_grid)
path_grid = astar.find_path(start_grid, goal_grid)

# --- Smoothing the path ---
# Assuming the path_grid is a list of (x, y) grid points, we can smooth it using the smooth_path function
smooth_path_grid = astar.smooth_path(path_grid, minx, miny, grid_spacing)

# --- Debug A* grid ---
astar_grid = astar.grid
astar_walkable = np.sum(astar_grid == 0)
astar_obstacle = np.sum(astar_grid == 1)
astar_padded = np.sum((astar_grid > 0) & (astar_grid < 1))
print(f"A* grid stats: {astar_walkable} walkable, {astar_obstacle} obstacle, {astar_padded} padded cells")

# --- Visualization ---
# Assuming astar_grid is your grid and path_grid is the original A* path
plt.figure(figsize=(10, 6))

# Plot the grid (the map) - 'gray' colormap for the map
plt.imshow(astar_grid, cmap='gray', origin='lower')

# Plot the original A* path (red line)
original_x, original_y = zip(*path_grid)
plt.plot(original_x, original_y, 'r-', label='A* Path', linewidth=2)

# Plot the smoothed path (blue line)
smooth_x, smooth_y = zip(*smooth_path_grid)
plt.plot(smooth_x, smooth_y, 'b-', label='Smoothed Path', linewidth=2)

# Highlight the start and goal points
plt.scatter(start_grid[0], start_grid[1], color='green', label='Start', zorder=5, s=100)
plt.scatter(goal_grid[0], goal_grid[1], color='red', label='Goal', zorder=5, s=100)

# Add a legend and title
plt.legend()
plt.title('A* Path with Smoothing')

# Show the plot
plt.show()


def save_smooth_path_to_geojson(path, path_file):
    """
    Saves the given path as a GeoJSON file.
    
    :param path: A list of (x, y) tuples representing the smooth path coordinates.
    :param path_file: The file path to save the GeoJSON data.
    """
    # Create a GeoJSON feature for the path
    path_line = geojson.LineString(path)
    feature = geojson.Feature(geometry=path_line, properties={})
    feature_collection = geojson.FeatureCollection([feature])
    
    # Save the path as a GeoJSON file
    with open(path_file, "w") as f:
        geojson.dump(feature_collection, f)
    print(f"Path saved to {path_file}")

def convert_grid_path_to_geojson_coords(grid_path, minx, miny, grid_spacing):
    """
    Converts a grid-based path to geographic/world coordinates (e.g., lon/lat or meters).

    :param grid_path: A list of (ix, iy) tuples in grid coordinates.
    :param minx: Minimum x (origin) in world coordinates.
    :param miny: Minimum y (origin) in world coordinates.
    :param grid_spacing: Distance between grid points in world units.
    :return: A list of (x, y) tuples in world coordinates.
    """
    return [grid_to_world(ix, iy, minx, miny, grid_spacing) for ix, iy in grid_path]# Convert from grid to world (geo) coordinates

geo_path = convert_grid_path_to_geojson_coords(smooth_path_grid, minx, miny, grid_spacing)

# Save the path to GeoJSON
save_smooth_path_to_geojson(geo_path, PATH_EXPORT)


