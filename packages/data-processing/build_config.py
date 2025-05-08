import json
import geojson
import numpy as np
from shapely.geometry import LineString, Polygon, Point
from shapely.strtree import STRtree
import os
import argparse
import sys

# Constants
GRID_SPACING = 0.00001  # ~1 meter
HALLWAY_RADIUS = 1.0    # ~2 meters
ENDPOINT_RADIUS = 1.5   # ~3 meters

# Helper functions
def rasterize_line(grid, minx, miny, grid_spacing, line, width=1, value=0, buildings=None):
    height, width_grid = grid.shape
    width = int(round(width))
    cells_changed = 0
    building_tree = STRtree(buildings) if buildings else None

    if line.length == 0:
        x, y = line.xy[0][0], line.xy[1][0]
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        pt = Point(x, y)
        building_indices = building_tree.query(pt) if building_tree else []
        inside_building = any(buildings[idx].contains(pt) or buildings[idx].exterior.distance(pt) < 1e-8 for idx in building_indices)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    if inside_building and grid[iiy, iix] == 1:
                        grid[iiy, iix] = value
                        cells_changed += 1
        return cells_changed

    num_points = int(line.length / grid_spacing) + 1
    if num_points == 1:
        x, y = line.xy[0][0], line.xy[1][0]
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        pt = Point(x, y)
        building_indices = building_tree.query(pt) if building_tree else []
        inside_building = any(buildings[idx].contains(pt) or buildings[idx].exterior.distance(pt) < 1e-8 for idx in building_indices)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    if inside_building and grid[iiy, iix] == 1:
                        grid[iiy, iix] = value
                        cells_changed += 1
        return cells_changed

    for i in range(num_points):
        pt = line.interpolate(i * line.length / (num_points - 1))
        x, y = pt.x, pt.y
        ix = int((x - minx) / grid_spacing)
        iy = int((y - miny) / grid_spacing)
        building_indices = building_tree.query(pt) if building_tree else []
        inside_building = any(buildings[idx].contains(pt) or buildings[idx].exterior.distance(pt) < 1e-8 for idx in building_indices)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                iix = ix + dx
                iiy = iy + dy
                if 0 <= iix < width_grid and 0 <= iiy < height:
                    if inside_building and grid[iiy, iix] == 1:
                        grid[iiy, iix] = value
                        cells_changed += 1
    return cells_changed

def get_walkable_neighbors(grid, ix, iy):
    if not (0 <= ix < grid.shape[1] and 0 <= iy < grid.shape[0]):
        return 0
    neighbors = [
        (ix + 1, iy), (ix - 1, iy), (ix, iy + 1), (ix, iy - 1),
        (ix + 1, iy + 1), (ix + 1, iy - 1), (ix - 1, iy + 1), (ix - 1, iy - 1)
    ]
    walkable_count = 0
    for nx, ny in neighbors:
        if 0 <= nx < grid.shape[1] and 0 <= ny < grid.shape[0]:
            if grid[ny, nx] == 0:
                walkable_count += 1
    return walkable_count

def is_dead_end(grid, ix, iy, coords, hallway_idx=None):
    walkable_count = get_walkable_neighbors(grid, ix, iy)
    if walkable_count < 2:
        context = f"hallway {hallway_idx}" if hallway_idx is not None else "unknown hallway"
        print(f"Dead-end detected at grid ({ix}, {iy}), coords {coords}, {context}, walkable neighbors: {walkable_count}")
        print("Surrounding cells:")
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = ix + dx, iy + dy
                if 0 <= nx < grid.shape[1] and 0 <= ny < grid.shape[0]:
                    print(f"({nx}, {ny}): {grid[ny, nx]}")
    return walkable_count < 2

def extend_endpoint_to_building(endpoint, hallway, is_start, max_dist, grid, minx, miny, grid_spacing, buildings):
    coords = list(hallway.coords)
    if is_start:
        p1, p2 = coords[1], coords[0]
    else:
        p1, p2 = coords[-2], coords[-1]
    
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = np.sqrt(dx**2 + dy**2)
    if length == 0:
        return Point(p2), False
    
    dx /= length
    dy /= length
    
    step_dist = grid_spacing
    current_dist = 0
    building_tree = STRtree(buildings)
    building_hit = None
    closest_dist = float('inf')
    closest_point = None
    inside_building = False

    # Extend until we hit a building and then continue until 2 walkable neighbors
    while current_dist <= max_dist:
        new_x = p2[0] + dx * current_dist
        new_y = p2[1] + dy * current_dist
        new_point = Point(new_x, new_y)
        ix = int((new_x - minx) / grid_spacing)
        iy = int((new_y - miny) / grid_spacing)

        # Check if we're inside or on the boundary of a building
        building_indices = building_tree.query(new_point)
        for idx in building_indices:
            building = buildings[idx]
            if building.contains(new_point) or building.exterior.distance(new_point) < grid_spacing:
                inside_building = True
                building_hit = building
                # Snap to the boundary if very close
                if not building.contains(new_point):
                    nearest = building.exterior.interpolate(building.exterior.project(new_point))
                    new_x, new_y = nearest.x, nearest.y
                    new_point = Point(new_x, new_y)
                    ix = int((new_x - minx) / grid_spacing)
                    iy = int((new_y - miny) / grid_spacing)
                # Extend further beyond the boundary to ensure connectivity
                current_dist += grid_spacing * 4  # Extend 4 cells
                new_x = p2[0] + dx * current_dist
                new_y = p2[1] + dy * current_dist
                new_point = Point(new_x, new_y)
                ix = int((new_x - minx) / grid_spacing)
                iy = int((new_y - miny) / grid_spacing)
                print(f"Snapped to building with bounds {building.bounds} at point {new_point.coords[0]}")
                break

        # Check walkable neighbors if we're inside or near a building
        if inside_building:
            if 0 <= ix < grid.shape[1] and 0 <= iy < grid.shape[0]:
                walkable_neighbors = get_walkable_neighbors(grid, ix, iy)
                if walkable_neighbors >= 2:
                    closest_dist = current_dist
                    closest_point = new_point
                    break

        closest_dist = current_dist
        closest_point = new_point
        current_dist += step_dist

    # If no point with 2 walkable neighbors, try perpendicular directions
    if not (closest_point and get_walkable_neighbors(grid, int((closest_point.x - minx) / grid_spacing), int((closest_point.y - miny) / grid_spacing)) >= 2):
        perp_dx, perp_dy = -dy, dx
        for direction in [(perp_dx, perp_dy), (-perp_dx, -perp_dy)]:
            current_dist = 0
            while current_dist <= max_dist:
                new_x = p2[0] + direction[0] * current_dist
                new_y = p2[1] + direction[1] * current_dist
                new_point = Point(new_x, new_y)
                ix = int((new_x - minx) / grid_spacing)
                iy = int((new_y - miny) / grid_spacing)

                building_indices = building_tree.query(new_point)
                inside_building = False
                for idx in building_indices:
                    building = buildings[idx]
                    if building.contains(new_point) or building.exterior.distance(new_point) < grid_spacing:
                        inside_building = True
                        building_hit = building
                        if not building.contains(new_point):
                            nearest = building.exterior.interpolate(building.exterior.project(new_point))
                            new_x, new_y = nearest.x, nearest.y
                            new_point = Point(new_x, new_y)
                            ix = int((new_x - minx) / grid_spacing)
                            iy = int((new_y - miny) / grid_spacing)
                        # Extend further beyond the boundary
                        current_dist += grid_spacing * 4
                        new_x = p2[0] + direction[0] * current_dist
                        new_y = p2[1] + direction[1] * current_dist
                        new_point = Point(new_x, new_y)
                        ix = int((new_x - minx) / grid_spacing)
                        iy = int((new_y - miny) / grid_spacing)
                        print(f"Snapped to building with bounds {building.bounds} at point {new_point.coords[0]} (perpendicular direction)")
                        break

                if inside_building:
                    if 0 <= ix < grid.shape[1] and 0 <= iy < grid.shape[0]:
                        walkable_neighbors = get_walkable_neighbors(grid, ix, iy)
                        if walkable_neighbors >= 2:
                            closest_dist = current_dist
                            closest_point = new_point
                            break

                closest_dist = current_dist
                closest_point = new_point
                current_dist += step_dist
            if closest_point and get_walkable_neighbors(grid, int((closest_point.x - minx) / grid_spacing), int((closest_point.y - miny) / grid_spacing)) >= 2:
                break

    if building_hit and closest_point:
        ix = int((closest_point.x - minx) / grid_spacing)
        iy = int((closest_point.y - miny) / grid_spacing)
        if 0 <= ix < grid.shape[1] and 0 <= iy < grid.shape[0]:
            return closest_point, True
    return Point(p2), False

def find_non_dead_end_point(endpoint, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=None):
    endpoint = Point(endpoint)
    for hallway in hallways:
        if hallway != exclude_hallway and (endpoint.distance(Point(hallway.coords[0])) < 1e-10 or endpoint.distance(Point(hallway.coords[-1])) < 1e-10):
            new_point, extended = extend_endpoint_to_building(endpoint, hallway, is_start=endpoint.distance(Point(hallway.coords[0])) < 1e-10, max_dist=0.0005, grid=grid, minx=minx, miny=miny, grid_spacing=grid_spacing, buildings=buildings)
            if extended:
                ix = int((new_point.x - minx) / grid_spacing)
                iy = int((new_point.y - miny) / grid_spacing)
                dist = endpoint.distance(new_point)
                print(f"Extended dead-end {endpoint.coords[0]} to {new_point.coords[0]} to reach building, distance: {dist:.8f}, walkable neighbors: {get_walkable_neighbors(grid, ix, iy)}")
                return new_point, True
    
    candidates = []
    min_feature_dist = float('inf')
    closest_feature = None
    feature_type = None
    for hallway in hallways:
        if hallway != exclude_hallway:
            dist = hallway.distance(endpoint)
            if dist < min_feature_dist:
                min_feature_dist = dist
                closest_feature = hallway
                feature_type = "hallway"
    for building in buildings:
        dist = building.exterior.distance(endpoint)
        if dist < min_feature_dist:
            min_feature_dist = dist
            closest_feature = building.exterior
            feature_type = "building"

    if min_feature_dist < 0.00004:
        if feature_type == "hallway":
            nearest = closest_feature.interpolate(closest_feature.project(endpoint))
            ix = int((nearest.x - minx) / grid_spacing)
            iy = int((nearest.y - miny) / grid_spacing)
            if get_walkable_neighbors(grid, ix, iy) >= 2:
                candidates.append((min_feature_dist, nearest))
        else:
            edge_length = closest_feature.length
            for t in np.linspace(0, edge_length, num=30):
                point = closest_feature.interpolate(t)
                dist_to_point = endpoint.distance(point)
                if dist_to_point < 0.00004:
                    ix = int((point.x - minx) / grid_spacing)
                    iy = int((point.y - miny) / grid_spacing)
                    if get_walkable_neighbors(grid, ix, iy) >= 2:
                        candidates.append((dist_to_point, point))

    if not candidates and min_feature_dist < 0.00006:
        print(f"Warning: Fallback to 6-meter radius for dead-end fix at {endpoint.coords[0]}")
        if feature_type == "hallway":
            nearest = closest_feature.interpolate(closest_feature.project(endpoint))
            ix = int((nearest.x - minx) / grid_spacing)
            iy = int((nearest.y - miny) / grid_spacing)
            if get_walkable_neighbors(grid, ix, iy) >= 2:
                candidates.append((min_feature_dist, nearest))
        else:
            edge_length = closest_feature.length
            for t in np.linspace(0, edge_length, num=30):
                point = closest_feature.interpolate(t)
                dist_to_point = endpoint.distance(point)
                if dist_to_point < 0.00006:
                    ix = int((point.x - minx) / grid_spacing)
                    iy = int((point.y - miny) / grid_spacing)
                    if get_walkable_neighbors(grid, ix, iy) >= 2:
                        candidates.append((dist_to_point, point))

    if not candidates:
        min_dist = float('inf')
        best_point = None
        ix_start = int((endpoint.x - minx) / grid_spacing)
        iy_start = int((endpoint.y - miny) / grid_spacing)
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                ix = ix_start + dx
                iy = iy_start + dy
                if 0 <= ix < grid.shape[1] and 0 <= iy < grid.shape[0]:
                    if grid[iy, ix] == 0 and get_walkable_neighbors(grid, ix, iy) >= 2:
                        x = minx + ix * grid_spacing + grid_spacing / 2
                        y = miny + iy * grid_spacing + grid_spacing / 2
                        point = Point(x, y)
                        dist = endpoint.distance(point)
                        if dist < min_dist:
                            min_dist = dist
                            best_point = point
        if best_point:
            candidates.append((min_dist, best_point))

    if candidates:
        candidates.sort()
        snapped_point = candidates[0][1]
        ix = int((snapped_point.x - minx) / grid_spacing)
        iy = int((snapped_point.y - miny) / grid_spacing)
        dist = endpoint.distance(snapped_point)
        print(f"Fixed dead-end {endpoint.coords[0]} to {snapped_point.coords[0]} on {feature_type or 'grid'}, distance: {dist:.8f}, walkable neighbors: {get_walkable_neighbors(grid, ix, iy)}")
        return snapped_point, True
    return endpoint, False

def rasterize_map(bounds_poly, buildings, hallways, grid_spacing, hallway_radius=1.0, endpoint_radius=1.0):
    minx, miny, maxx, maxy = bounds_poly.bounds
    width = int(np.ceil((maxx - minx) / grid_spacing))
    height = int(np.ceil((maxy - miny) / grid_spacing))
    grid = np.ones((height, width), dtype=np.uint8)  # Initialize as obstacles

    print(f"Initializing grid within Bounds: {bounds_poly.bounds}")
    minx_b, miny_b, maxx_b, maxy_b = bounds_poly.bounds
    min_ix = max(0, int((minx_b - minx) / grid_spacing))
    max_ix = min(width, int((maxx_b - minx) / grid_spacing) + 1)
    min_iy = max(0, int((miny_b - miny) / grid_spacing))
    max_iy = min(height, int((maxy_b - miny) / grid_spacing) + 1)
    walkable_cells = 0
    for iy in range(min_iy, max_iy):
        for ix in range(min_ix, max_ix):
            x = minx + ix * grid_spacing + grid_spacing / 2
            y = miny + iy * grid_spacing + grid_spacing / 2
            pt = Point(x, y)
            if bounds_poly.contains(pt):
                grid[iy, ix] = 0
                walkable_cells += 1
    print(f"Initial walkable cells within Bounds: {walkable_cells}")

    building_tree = STRtree(buildings)
    building_cell_counts = []
    for b in buildings:
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
    print(f"Total obstacle cells after buildings: {np.sum(grid == 1)}")
    print(f"Walkable cells after buildings: {np.sum(grid == 0)}")

    for idx, hallway in enumerate(hallways):
        building_indices = building_tree.query(hallway)
        intersects_building = any(buildings[idx].intersects(hallway) for idx in building_indices)
        if not intersects_building:
            print(f"Hallway {idx} does not intersect any building, skipping...")
            continue
        cells = rasterize_line(grid, minx, miny, grid_spacing, hallway, width=hallway_radius, value=0, buildings=buildings)
        print(f"Rasterized hallway {idx} inside building, changed {cells} cells")

    fixed_hallways = []
    for idx, hallway in enumerate(hallways):
        building_indices = building_tree.query(hallway)
        if not any(buildings[idx].intersects(hallway) for idx in building_indices):
            continue

        start_point = Point(hallway.coords[0])
        end_point = Point(hallway.coords[-1])
        new_coords = list(hallway.coords)

        ix = int((start_point.x - minx) / grid_spacing)
        iy = int((start_point.y - miny) / grid_spacing)
        if is_dead_end(grid, ix, iy, start_point.coords[0], idx):
            new_point, extended = extend_endpoint_to_building(start_point, hallway, is_start=True, max_dist=0.0005, grid=grid, minx=minx, miny=miny, grid_spacing=grid_spacing, buildings=buildings)
            if extended:
                new_coords.insert(0, new_point.coords[0])
                ix_new = int((new_point.x - minx) / grid_spacing)
                iy_new = int((new_point.y - miny) / grid_spacing)
                print(f"Extended dead-end start at {start_point.coords[0]} to {new_point.coords[0]} to reach building, walkable neighbors: {get_walkable_neighbors(grid, ix_new, iy_new)}, hallway {idx}")
                segment = LineString([new_coords[1], new_coords[0]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                print(f"Rasterized start endpoint segment, changed {cells} cells, hallway {idx}")
            else:
                print(f"Warning: Extension failed for dead-end start at {start_point.coords[0]}, hallway {idx}")
                snapped_point, snapped = find_non_dead_end_point(start_point, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
                if snapped:
                    new_coords.insert(0, snapped_point.coords[0])
                    print(f"Fixed dead-end start at {start_point.coords[0]} to {snapped_point.coords[0]} via snapping, hallway {idx}")
                    segment = LineString([new_coords[1], new_coords[0]])
                    cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                    print(f"Rasterized start endpoint segment, changed {cells} cells, hallway {idx}")

        ix = int((end_point.x - minx) / grid_spacing)
        iy = int((end_point.y - miny) / grid_spacing)
        if is_dead_end(grid, ix, iy, end_point.coords[0], idx):
            new_point, extended = extend_endpoint_to_building(end_point, hallway, is_start=False, max_dist=0.0005, grid=grid, minx=minx, miny=miny, grid_spacing=grid_spacing, buildings=buildings)
            if extended:
                new_coords.append(new_point.coords[0])
                ix_new = int((new_point.x - minx) / grid_spacing)
                iy_new = int((new_point.y - miny) / grid_spacing)
                print(f"Extended dead-end end at {end_point.coords[0]} to {new_point.coords[0]} to reach building, walkable neighbors: {get_walkable_neighbors(grid, ix_new, iy_new)}, hallway {idx}")
                segment = LineString([new_coords[-2], new_coords[-1]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                print(f"Rasterized end endpoint segment, changed {cells} cells, hallway {idx}")
            else:
                print(f"Warning: Extension failed for dead-end end at {end_point.coords[0]}, hallway {idx}")
                snapped_point, snapped = find_non_dead_end_point(end_point, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
                if snapped:
                    new_coords.append(snapped_point.coords[0])
                    print(f"Fixed dead-end end at {end_point.coords[0]} to {snapped_point.coords[0]} via snapping, hallway {idx}")
                    segment = LineString([new_coords[-2], new_coords[-1]])
                    cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                    print(f"Rasterized end endpoint segment, changed {cells} cells, hallway {idx}")

        fixed_hallways.append(LineString(new_coords))

    for idx, hallway in enumerate(fixed_hallways):
        cells = rasterize_line(grid, minx, miny, grid_spacing, hallway, width=hallway_radius, value=0, buildings=buildings)
        print(f"Re-rasterized hallway {idx} inside building, changed {cells} cells")
        start_point = Point(hallway.coords[0])
        end_point = Point(hallway.coords[-1])
        start_segment = LineString([hallway.coords[1], hallway.coords[0]])
        end_segment = LineString([hallway.coords[-2], hallway.coords[-1]])
        cells_start = rasterize_line(grid, minx, miny, grid_spacing, start_segment, width=endpoint_radius, value=0, buildings=buildings)
        cells_end = rasterize_line(grid, minx, miny, grid_spacing, end_segment, width=endpoint_radius, value=0, buildings=buildings)
        print(f"Rasterizing endpoint {start_point.coords[0]} with radius {endpoint_radius}, changed {cells_start} cells, hallway {idx}")
        print(f"Rasterizing endpoint {end_point.coords[0]} with radius {endpoint_radius}, changed {cells_end} cells, hallway {idx}")

    print("Starting final dead-end validation")
    for idx, hallway in enumerate(fixed_hallways):
        start_point = Point(hallway.coords[0])
        end_point = Point(hallway.coords[-1])
        ix_start = int((start_point.x - minx) / grid_spacing)
        iy_start = int((start_point.y - miny) / grid_spacing)
        ix_end = int((end_point.x - minx) / grid_spacing)
        iy_end = int((end_point.y - miny) / grid_spacing)
        new_coords = list(hallway.coords)
        modified = False
        if is_dead_end(grid, ix_start, iy_start, start_point.coords[0], idx):
            print(f"Validation failed: Dead-end persists at start {start_point.coords[0]}, hallway {idx}")
            snapped_point, snapped = find_non_dead_end_point(start_point, fixed_hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
            if snapped:
                new_coords.insert(0, snapped_point.coords[0])
                print(f"Fixed persistent dead-end start at {start_point.coords[0]} to {snapped_point.coords[0]} via snapping, hallway {idx}")
                segment = LineString([new_coords[1], new_coords[0]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                print(f"Rasterized start endpoint segment, changed {cells} cells, hallway {idx}")
                modified = True
        if is_dead_end(grid, ix_end, iy_end, end_point.coords[0], idx):
            print(f"Validation failed: Dead-end persists at end {end_point.coords[0]}, hallway {idx}")
            snapped_point, snapped = find_non_dead_end_point(end_point, fixed_hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
            if snapped:
                new_coords.append(snapped_point.coords[0])
                print(f"Fixed persistent dead-end end at {end_point.coords[0]} to {snapped_point.coords[0]} via snapping, hallway {idx}")
                segment = LineString([new_coords[-2], new_coords[-1]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=endpoint_radius, value=0, buildings=buildings)
                print(f"Rasterized end endpoint segment, changed {cells} cells, hallway {idx}")
                modified = True
        if modified:
            fixed_hallways[idx] = LineString(new_coords)

    print(f"Final walkable cells: {np.sum(grid == 0)}")
    print(f"Final obstacle cells: {np.sum(grid == 1)}")
    return grid, minx, miny, grid_spacing

def snap_endpoint(endpoint, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=None):
    endpoint = Point(endpoint)
    for hallway in hallways:
        if hallway != exclude_hallway and (endpoint.distance(Point(hallway.coords[0])) < 1e-10 or endpoint.distance(Point(hallway.coords[-1])) < 1e-10):
            new_point, extended = extend_endpoint_to_building(endpoint, hallway, is_start=endpoint.distance(Point(hallway.coords[0])) < 1e-10, max_dist=0.0005, grid=grid, minx=minx, miny=miny, grid_spacing=grid_spacing, buildings=buildings)
            if extended:
                ix = int((new_point.x - minx) / grid_spacing)
                iy = int((new_point.y - miny) / grid_spacing)
                dist = endpoint.distance(new_point)
                print(f"Extended {endpoint.coords[0]} to {new_point.coords[0]} to reach building, distance: {dist:.8f}, walkable neighbors: {get_walkable_neighbors(grid, ix, iy)}")
                return new_point, True
    
    candidates = []
    min_feature_dist = float('inf')
    closest_feature = None
    feature_type = None
    for hallway in hallways:
        if hallway != exclude_hallway:
            dist = hallway.distance(endpoint)
            if dist < min_feature_dist:
                min_feature_dist = dist
                closest_feature = hallway
                feature_type = "hallway"
    for building in buildings:
        dist = building.exterior.distance(endpoint)
        if dist < min_feature_dist:
            min_feature_dist = dist
            closest_feature = building.exterior
            feature_type = "building"

    if min_feature_dist < 0.00004:
        if feature_type == "hallway":
            nearest = closest_feature.interpolate(closest_feature.project(endpoint))
            ix = int((nearest.x - minx) / grid_spacing)
            iy = int((nearest.y - miny) / grid_spacing)
            if get_walkable_neighbors(grid, ix, iy) >= 2:
                candidates.append((min_feature_dist, nearest))
        else:
            edge_length = closest_feature.length
            for t in np.linspace(0, edge_length, num=30):
                point = closest_feature.interpolate(t)
                dist_to_point = endpoint.distance(point)
                if dist_to_point < 0.00004:
                    ix = int((point.x - minx) / grid_spacing)
                    iy = int((point.y - miny) / grid_spacing)
                    if get_walkable_neighbors(grid, ix, iy) >= 2:
                        candidates.append((dist_to_point, point))

    if not candidates and min_feature_dist < 0.00006:
        print(f"Warning: Fallback to 6-meter radius for endpoint {endpoint.coords[0]}")
        if feature_type == "hallway":
            nearest = closest_feature.interpolate(closest_feature.project(endpoint))
            ix = int((nearest.x - minx) / grid_spacing)
            iy = int((nearest.y - miny) / grid_spacing)
            if get_walkable_neighbors(grid, ix, iy) >= 2:
                candidates.append((min_feature_dist, nearest))
        else:
            edge_length = closest_feature.length
            for t in np.linspace(0, edge_length, num=30):
                point = closest_feature.interpolate(t)
                dist_to_point = endpoint.distance(point)
                if dist_to_point < 0.00006:
                    ix = int((point.x - minx) / grid_spacing)
                    iy = int((point.y - miny) / grid_spacing)
                    if get_walkable_neighbors(grid, ix, iy) >= 2:
                        candidates.append((dist_to_point, point))

    if candidates:
        candidates.sort()
        snapped_point = candidates[0][1]
        ix = int((snapped_point.x - minx) / grid_spacing)
        iy = int((snapped_point.y - miny) / grid_spacing)
        dist = endpoint.distance(snapped_point)
        print(f"Snapped {endpoint.coords[0]} to {snapped_point.coords[0]} on {feature_type}, distance: {dist:.8f}, walkable neighbors: {get_walkable_neighbors(grid, ix, iy)}")
        return snapped_point, True
    return endpoint, False

def check_and_snap_hallways(hallways, buildings, grid, minx, miny, grid_spacing):
    snapped_hallways = []
    building_tree = STRtree(buildings)
    for idx, hallway in enumerate(hallways):
        building_indices = building_tree.query(hallway)
        if not any(buildings[idx].intersects(hallway) for idx in building_indices):
            print(f"Hallway {idx} does not intersect any building, skipping in snapping phase...")
            continue

        start_point = Point(hallway.coords[0])
        end_point = Point(hallway.coords[-1])
        is_valid_start = False
        is_valid_end = False

        ix_start = int((start_point.x - minx) / grid_spacing)
        iy_start = int((start_point.y - miny) / grid_spacing)
        ix_end = int((end_point.x - minx) / grid_spacing)
        iy_end = int((end_point.y - miny) / grid_spacing)
        for other_hallway in hallways:
            if hallway != other_hallway:
                if other_hallway.distance(start_point) < 0.00002 and not is_dead_end(grid, ix_start, iy_start, start_point.coords[0], idx):
                    is_valid_start = True
                if other_hallway.distance(end_point) < 0.00002 and not is_dead_end(grid, ix_end, iy_end, end_point.coords[0], idx):
                    is_valid_end = True
        for building in buildings:
            if building.exterior.distance(start_point) < 0.00002 and not is_dead_end(grid, ix_start, iy_start, start_point.coords[0], idx):
                is_valid_start = True
            if building.exterior.distance(end_point) < 0.00002 and not is_dead_end(grid, ix_end, iy_end, end_point.coords[0], idx):
                is_valid_end = True

        new_coords = list(hallway.coords)
        if not is_valid_start:
            new_start, extended = snap_endpoint(start_point, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
            if extended:
                new_coords.insert(0, new_start.coords[0])
                print(f"Extended start of hallway to {new_start.coords[0]}, hallway {idx}")
                segment = LineString([new_coords[1], new_coords[0]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=ENDPOINT_RADIUS, value=0, buildings=buildings)
                print(f"Rasterized start endpoint segment, changed {cells} cells, hallway {idx}")
        if not is_valid_end:
            new_end, extended = snap_endpoint(end_point, hallways, buildings, grid, minx, miny, grid_spacing, exclude_hallway=hallway)
            if extended:
                new_coords.append(new_end.coords[0])
                print(f"Extended end of hallway to {new_end.coords[0]}, hallway {idx}")
                segment = LineString([new_coords[-2], new_coords[-1]])
                cells = rasterize_line(grid, minx, miny, grid_spacing, segment, width=ENDPOINT_RADIUS, value=0, buildings=buildings)
                print(f"Rasterized end endpoint segment, changed {cells} cells, hallway {idx}")

        snapped_hallways.append(LineString(new_coords))

    return snapped_hallways

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build grid configuration from GeoJSON")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_GEOJSON_PATH = os.path.join(SCRIPT_DIR, "Full.geojson")
    parser.add_argument('--input', type=str, default=DEFAULT_GEOJSON_PATH,
                        help='Path to input GeoJSON file')
    parser.add_argument('--output', type=str, default=os.path.join(SCRIPT_DIR, "grid_config.json"),
                        help='Path to output JSON file')
    args = parser.parse_args()

    input_geojson_path = "Full.geojson"
    output_json_path = "grid_config_gu.json"

    if not os.path.exists(input_geojson_path):
        print(f"Error: GeoJSON file not found: {input_geojson_path}")
        sys.exit(1)

    with open(input_geojson_path, "r") as f:
        gj = geojson.load(f)

    buildings = []
    building_labels = []
    hallways = []
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
            pass

    if bounds_poly is None:
        print("Error: No 'Bounds' polygon found in GeoJSON")
        sys.exit(1)

    print(f"Loaded {len(buildings)} buildings, {len(hallways)} hallways.")

    minx, miny, maxx, maxy = bounds_poly.bounds
    width = int(np.ceil((maxx - minx) / GRID_SPACING))
    height = int(np.ceil((maxy - miny) / GRID_SPACING))
    grid = np.ones((height, width), dtype=np.uint8)

    minx_b, miny_b, maxx_b, maxy_b = bounds_poly.bounds
    min_ix = max(0, int((minx_b - minx) / GRID_SPACING))
    max_ix = min(width, int((maxx_b - minx) / GRID_SPACING) + 1)
    min_iy = max(0, int((miny_b - miny) / GRID_SPACING))
    max_iy = min(height, int((maxy_b - miny) / GRID_SPACING) + 1)
    walkable_cells = 0
    for iy in range(min_iy, max_iy):
        for ix in range(min_ix, max_ix):
            x = minx + ix * GRID_SPACING + GRID_SPACING / 2
            y = miny + iy * GRID_SPACING + GRID_SPACING / 2
            pt = Point(x, y)
            if bounds_poly.contains(pt):
                grid[iy, ix] = 0
                walkable_cells += 1
    print(f"Initial walkable cells within Bounds: {walkable_cells}")

    building_tree = STRtree(buildings)
    for b in buildings:
        minx_b, miny_b, maxx_b, maxy_b = b.bounds
        min_ix = max(0, int((minx_b - minx) / GRID_SPACING))
        max_ix = min(width, int((maxx_b - minx) / GRID_SPACING) + 1)
        min_iy = max(0, int((miny_b - miny) / GRID_SPACING))
        max_iy = min(height, int((maxy_b - miny) / GRID_SPACING) + 1)
        for iy in range(min_iy, max_iy):
            for ix in range(min_ix, max_ix):
                x = minx + ix * GRID_SPACING + GRID_SPACING / 2
                y = miny + iy * GRID_SPACING + GRID_SPACING / 2
                pt = Point(x, y)
                if b.contains(pt):
                    grid[iy, ix] = 1
    print(f"Walkable cells after buildings: {np.sum(grid == 0)}")

    snapped_hallways = check_and_snap_hallways(hallways, buildings, grid, minx, miny, GRID_SPACING)
    print(f"Processed {len(snapped_hallways)} hallways, extended endpoints where needed.")

    grid, minx, miny, grid_spacing = rasterize_map(
        bounds_poly, buildings, snapped_hallways, GRID_SPACING, HALLWAY_RADIUS, ENDPOINT_RADIUS
    )

    grid_list = grid.tolist()

    output_json = {
        "rows": grid.shape[0],
        "cols": grid.shape[1],
        "lat_min": miny,
        "lat_max": miny + grid.shape[0] * grid_spacing,
        "lng_min": minx,
        "lng_max": minx + grid.shape[1] * grid_spacing,
        "grid": grid_list,
        "buildings": building_labels
    }

    with open(output_json_path, 'w') as file:
        json.dump(output_json, file, indent=2)

    print(f"Grid configuration saved to {output_json_path}")
    print(f"Grid shape: {grid.shape[0]}x{grid.shape[1]}")
    print(f"Walkable cells: {np.sum(grid == 0)}")
    print(f"Obstacle cells: {np.sum(grid == 1)}")