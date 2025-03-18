import heapq
import math

# Global padding variable
# This creates a small buffer around all obstacles to allow for smoother pathfinding
padding = 2

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
    
    # Then add padding around obstacles
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 1:
                # Mark cells within padding_value distance as obstacles
                for di in range(-padding_value, padding_value + 1):
                    for dj in range(-padding_value, padding_value + 1):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols:
                            padded_grid[ni][nj] = 1
    
    return padded_grid

def a_star(grid, start, end, custom_padding=None):
    """Performs A* pathfinding algorithm to find the shortest path from start to end."""
    global padding
    
    # Apply padding around obstacles
    pad_value = custom_padding if custom_padding is not None else padding
    if pad_value > 0:
        working_grid = apply_padding(grid, pad_value)
    else:
        working_grid = grid
    
    rows, cols = len(working_grid), len(working_grid[0])
    
    # Ensure start and end positions are not within padded areas
    if working_grid[start[0]][start[1]] == 1 or working_grid[end[0]][end[1]] == 1:
        return []  # Start or end position is not traversable
    
    open_set = []  # Priority queue for A* search
    heapq.heappush(open_set, (0, start))  # (cost, (x, y))
    
    came_from = {}  # Stores the path
    g_score = {start: 0}  # Cost from start to current node
    f_score = {start: euclidean_distance(start, end)}  # Estimated cost from start to end
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (1, -1), (-1, 1), (-1, -1)]  # Up, Down, Left, Right, Diagonals
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Return reversed path
        
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and working_grid[neighbor[0]][neighbor[1]] == 0:
                tentative_g_score = g_score[current] + euclidean_distance(current, neighbor)
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + euclidean_distance(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return []  # No path found