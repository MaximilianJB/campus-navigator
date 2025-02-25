import heapq
import math

def euclidean_distance(a, b):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def a_star(grid, start, end):
    """Performs A* pathfinding algorithm to find the shortest path from start to end."""
    rows, cols = len(grid), len(grid[0])
    
    if grid[start[0]][start[1]] == 1 or grid[end[0]][end[1]] == 1:
        return []  # Start or end position is not traversable
    
    open_set = []  # Priority queue for A* search
    heapq.heappush(open_set, (0, start))  # (cost, (x, y))
    
    came_from = {}  # Stores the path
    g_score = {start: 0}  # Cost from start to current node
    f_score = {start: euclidean_distance(start, end)}  # Estimated cost from start to end
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
    
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
            
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and grid[neighbor[0]][neighbor[1]] == 0:
                tentative_g_score = g_score[current] + euclidean_distance(current, neighbor)
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + euclidean_distance(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return []  # No path found
