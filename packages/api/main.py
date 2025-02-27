import heapq
import math
import json
from flask import Flask, request, make_response, jsonify
from google.cloud import storage

app = Flask(__name__)

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

def lat_lng_to_grid(lat, lng, config):
    """Convert lat-long to grid coordinates."""
    row_size = (config['lat_max'] - config['lat_min']) / config['rows']
    col_size = (config['lng_max'] - config['lng_min']) / config['cols']
    row = int((config['lat_max'] - lat) / row_size)
    col = int((lng - config['lng_min']) / col_size)
    return row, col

def grid_to_lat_lng(row, col, config):
    """Convert grid coordinates to lat-long (center of cell)."""
    row_size = (config['lat_max'] - config['lat_min']) / config['rows']
    col_size = (config['lng_max'] - config['lng_min']) / config['cols']
    lat = config['lat_max'] - (row + 0.5) * row_size
    lng = config['lng_min'] + (col + 0.5) * col_size
    return lat, lng

def download_grid_config(bucket_name, file_name):
    """Download and parse grid_config.json from Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    return json.loads(blob.download_as_text())

# Cloud Run HTTP Handler with manual CORS
@app.route('/', methods=['OPTIONS', 'POST'])
def find_path():
    """Handle POST requests to find a path and OPTIONS for CORS preflight."""
    # Define allowed origins
    allowed_origins = ['http://localhost:3000', 'https://campus-navigator.vercel.app']
    origin = request.headers.get('Origin', '')  # Get the Origin header from the request
    cors_origin = origin if origin in allowed_origins else 'https://campus-navigator.vercel.app'  # Default to Vercel

    # Set CORS headers for all responses
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = cors_origin

    if request.method == 'OPTIONS':
        # Handle preflight request
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight for 1 hour
        return response, 204

    # Handle POST request
    if request.method != 'POST':
        response = make_response(jsonify({'error': 'Method not allowed'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 405

    # Parse request JSON
    data = request.get_json()
    if not data or 'start_lat' not in data or 'start_lng' not in data or 'end_lat' not in data or 'end_lng' not in data:
        response = make_response(jsonify({'error': 'Missing required fields: start_lat, start_lng, end_lat, end_lng'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 400
    
    start_lat = float(data['start_lat'])
    start_lng = float(data['start_lng'])
    end_lat = float(data['end_lat'])
    end_lng = float(data['end_lng'])
    
    # Load grid config from Cloud Storage
    try:
        config = download_grid_config('gu-campus-maps', 'grid_config.json')
    except Exception as e:
        response = make_response(jsonify({'error': f'Failed to load grid config: {str(e)}'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 500
    
    # Convert lat-long to grid coordinates
    start_row, start_col = lat_lng_to_grid(start_lat, start_lng, config)
    end_row, end_col = lat_lng_to_grid(end_lat, end_lng, config)
    
    # Validate coordinates
    if not (0 <= start_row < config['rows'] and 0 <= start_col < config['cols']):
        response = make_response(jsonify({'error': 'Start point outside grid bounds'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 400
    if not (0 <= end_row < config['rows'] and 0 <= end_col < config['cols']):
        response = make_response(jsonify({'error': 'End point outside grid bounds'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 400
    if config['grid'][start_row][start_col] == 1:
        response = make_response(jsonify({'error': 'Start point is an obstacle'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 400
    if config['grid'][end_row][end_col] == 1:
        response = make_response(jsonify({'error': 'End point is an obstacle'}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 400
    
    # Run A* pathfinding
    path = a_star(config['grid'], (start_row, start_col), (end_row, end_col))
    if not path:
        response = make_response(jsonify({'path': []}))
        response.headers['Access-Control-Allow-Origin'] = cors_origin
        return response, 200
    
    # Convert path to lat-long
    path_lat_lng = [grid_to_lat_lng(row, col, config) for row, col in path]
    response = make_response(jsonify({'path': [[lat, lng] for lat, lng in path_lat_lng]}))
    response.headers['Access-Control-Allow-Origin'] = cors_origin
    return response, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)