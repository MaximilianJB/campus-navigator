import heapq
import math
from path_smoothing import get_smooth_path_points

# Global padding variable
# This creates a small buffer around all obstacles to allow for smoother pathfinding
padding = 2  # Reduced padding to allow closer approach to buildings

def euclidean_distance(a, b):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def apply_padding(grid, padding_value):
    """Create a new grid with padding around obstacles."""
    if padding_value <= 0:
        return grid

    rows, cols = len(grid), len(grid[0])
    padded_grid = [[0 for _ in range(cols)] for _ in range(rows)]
    
    # First copy the original obstacles
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 1:
                padded_grid[i][j] = 1
    
    # Then add padding around obstacles, but with decreasing values
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 1:
                # Mark cells within padding_value distance with decreasing values
                for di in range(-padding_value, padding_value + 1):
                    for dj in range(-padding_value, padding_value + 1):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols:
                            # Calculate distance from obstacle
                            dist = max(abs(di), abs(dj))
                            # Convert distance to a value between 0 and 1
                            # Closer to obstacle = higher value
                            if padded_grid[ni][nj] != 1:  # Don't override actual obstacles
                                padded_grid[ni][nj] = (padding_value - dist + 1) / (padding_value + 1)
    
    return padded_grid

def get_neighbors(current, grid):
    """Get valid neighboring cells."""
    rows, cols = len(grid), len(grid[0])
    row, col = current
    
    # Include diagonal movements
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    neighbors = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if (0 <= r < rows and 0 <= c < cols and grid[r][c] != 1):
            # Add neighbor with its padding value as additional cost
            neighbors.append((r, c))
    
    return neighbors

def a_star(grid, start, end, custom_padding=None):
    """Performs A* pathfinding algorithm with cost influenced by padding."""
    if not grid or not (0 <= start[0] < len(grid)) or not (0 <= start[1] < len(grid[0])) or \
       not (0 <= end[0] < len(grid)) or not (0 <= end[1] < len(grid[0])):
        return None

    # Check if start or end is in padded area but not an actual obstacle
    if grid[start[0]][start[1]] == 1 or grid[end[0]][end[1]] == 1:
        return None

    rows, cols = len(grid), len(grid[0])
    closed_set = set()
    open_set = [(0, start)]
    heapq.heapify(open_set)
    came_from = {}
    g_score = {start: 0}
    f_score = {start: euclidean_distance(start, end)}
    
    while open_set:
        current_f, current = heapq.heappop(open_set)
        
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            
            # smooth the path using spline logic
            smoothed_path = get_smooth_path_points(path, cell_size=2, smoothing_factor=0.5)
            return smoothed_path
            
        closed_set.add(current)
        
        for neighbor in get_neighbors(current, grid):
            if neighbor in closed_set:
                continue
                
            # Calculate cost including padding penalty
            padding_cost = grid[neighbor[0]][neighbor[1]] if isinstance(grid[neighbor[0]][neighbor[1]], float) else 0
            tentative_g = g_score[current] + euclidean_distance(current, neighbor) + padding_cost * 2
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = g_score[neighbor] + euclidean_distance(neighbor, end)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None