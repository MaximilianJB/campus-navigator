import heapq
import math
import numpy as np

def euclidean_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def apply_padding(grid, padding_value=2):
    if padding_value <= 0:
        return grid
    padded_grid = grid.copy().astype(float)
    height, width = grid.shape
    for i in range(height):
        for j in range(width):
            if grid[i, j] == 1:
                for di in range(-padding_value, padding_value + 1):
                    for dj in range(-padding_value, padding_value + 1):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < height and 0 <= nj < width:
                            dist = max(abs(di), abs(dj))
                            if padded_grid[ni, nj] != 1:
                                # Higher cost closer to obstacles (0.75 at dist=1, 0.5 at dist=2)
                                padded_grid[ni, nj] = max(padded_grid[ni, nj], (padding_value - dist + 1) / (padding_value + 1))
    return padded_grid

def get_neighbors(current, grid, debug=False):
    height, width = grid.shape
    x, y = current
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    neighbors = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= ny < height and 0 <= nx < width and grid[ny, nx] != 1:
            neighbors.append((nx, ny))
    if debug:
        if not neighbors:
            print(f"No neighbors for {current}. Grid values around ({x}, {y}):")
            for dy in range(-2, 3):
                row = []
                for dx in range(-2, 3):
                    nx, ny = x + dx, y + dy
                    if 0 <= ny < height and 0 <= nx < width:
                        row.append(grid[ny, nx])
                    else:
                        row.append("X")
                print(row)
        else:
            print(f"Neighbors for {current}: {neighbors}")
    return neighbors

def line_of_sight(grid, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy)) + 1
    if steps <= 1:
        return True
    for i in range(steps):
        t = i / (steps - 1)
        x = int(x1 + t * dx)
        y = int(y1 + t * dy)
        if not (0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]) or grid[y, x] == 1:
            return False
    return True

def reduce_waypoints(path, grid):
    if len(path) < 3:
        return path
    reduced = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if line_of_sight(grid, path[i], path[j]):
                reduced.append(path[j])
                i = j
                break
            j -= 1
        else:
            reduced.append(path[i + 1])
            i += 1
    return reduced

class AStar:
    def __init__(self, grid):
        self.grid = apply_padding(grid, padding_value=2)  # ~4 meters padding
        self.np_grid = grid.copy()
        self.explored = set()

    def is_hallway_like(self, ix, iy):
        """Check if a cell is hallway-like (traversable with obstacles nearby)."""
        if self.np_grid[iy, ix] != 0:
            return False
        height, width = self.np_grid.shape
        obstacle_count = 0
        max_dist = 3  # Check 3 cells (~6 meters) for obstacles
        for di in range(-max_dist, max_dist + 1):
            for dj in range(-max_dist, max_dist + 1):
                ni, nj = iy + di, ix + dj
                if 0 <= ni < height and 0 <= nj < width and self.np_grid[ni, nj] == 1:
                    obstacle_count += 1
        # Hallway-like if surrounded by obstacles (e.g., >= 4 obstacles in 7x7 grid)
        return obstacle_count >= 4

    def find_path(self, start, end):
        height, width = self.grid.shape
        if not (0 <= start[0] < width and 0 <= start[1] < height) or \
           not (0 <= end[0] < width and 0 <= end[1] < height):
            print("Start or end out of bounds")
            return None
        if self.grid[start[1], start[0]] == 1 or self.grid[end[1], end[0]] == 1:
            print("Start or end in obstacle")
            return None

        print(f"Grid at start ({start[0]}, {start[1]}): {self.grid[start[1], start[0]]}")
        print(f"Grid at goal ({end[0]}, {end[1]}): {self.grid[end[1], end[0]]}")
        start_neighbors = get_neighbors(start, self.grid, debug=True)
        end_neighbors = get_neighbors(end, self.grid, debug=True)

        self.explored = set()
        closed_set = set()
        open_set = [(0, start)]
        heapq.heapify(open_set)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: euclidean_distance(start, end)}
        iteration = 0

        while open_set:
            iteration += 1
            current_f, current = heapq.heappop(open_set)
            self.explored.add(current)

            if iteration % 1000 == 0:
                print(f"Iteration {iteration}: Explored {len(self.explored)} nodes, Open set size: {len(open_set)}")

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                print(f"Path found after {iteration} iterations")
                return path

            closed_set.add(current)
            for neighbor in get_neighbors(current, self.grid):
                if neighbor in closed_set:
                    continue
                # Prefer hallway-like cells, override padding costs
                move_cost = 0.1 if self.is_hallway_like(neighbor[0], neighbor[1]) else max(1.0, self.grid[neighbor[1], neighbor[0]])
                tentative_g = g_score[current] + euclidean_distance(current, neighbor) * move_cost
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = g_score[neighbor] + euclidean_distance(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        print(f"No path found after {iteration} iterations")
        return None

    def smooth_path(self, path_points, smoothing_factor=0.2, num_points=200):
        if len(path_points) < 3:
            return path_points

        reduced_path = reduce_waypoints(path_points, self.np_grid)
        print(f"Reduced path from {len(path_points)} to {len(reduced_path)} points")

        # Linear interpolation in grid coordinates
        smoothed_points = []
        for i in range(len(reduced_path) - 1):
            p1 = reduced_path[i]
            p2 = reduced_path[i + 1]
            steps = int(euclidean_distance(p1, p2) / smoothing_factor) + 1
            for j in range(steps):
                t = j / steps
                x = p1[0] + t * (p2[0] - p1[0])
                y = p1[1] + t * (p2[1] - p1[1])
                ix, iy = int(round(x)), int(round(y))
                if 0 <= iy < self.np_grid.shape[0] and 0 <= ix < self.np_grid.shape[1]:
                    if self.np_grid[iy, ix] == 0 and self.is_hallway_like(ix, iy):
                        smoothed_points.append((ix, iy))
                    else:
                        # Find nearest hallway-like cell
                        for di in range(-2, 3):
                            for dj in range(-2, 3):
                                ni, nj = iy + di, ix + dj
                                if (
                                    0 <= ni < self.np_grid.shape[0]
                                    and 0 <= nj < self.np_grid.shape[1]
                                    and self.np_grid[ni, nj] == 0
                                    and self.is_hallway_like(nj, ni)
                                ):
                                    smoothed_points.append((nj, ni))
                                    break
                            else:
                                continue
                            break
                        else:
                            # Fallback to any traversable cell
                            if self.np_grid[iy, ix] == 0:
                                smoothed_points.append((ix, iy))

        # Remove duplicates
        seen = set()
        unique_points = []
        for pt in smoothed_points:
            if pt not in seen:
                seen.add(pt)
                unique_points.append(pt)

        # Validate line-of-sight
        valid = True
        for i in range(1, len(unique_points)):
            if not line_of_sight(self.np_grid, unique_points[i - 1], unique_points[i]):
                valid = False
                print("Smoothed path failed line-of-sight check.")
                break

        return unique_points if valid else reduced_path