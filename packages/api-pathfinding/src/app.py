"""
Flask application for pathfinding API
"""
import json
from flask import Flask, request, make_response, jsonify
from src.utils import a_star, lat_lng_to_grid, grid_to_lat_lng, find_nearest_valid_point
from src.storage import download_grid_config, DEFAULT_BUCKET_NAME

app = Flask(__name__)

# Define allowed origins for CORS
ALLOWED_ORIGINS = ['http://localhost:3000', 'https://campus-navigator.vercel.app']

def get_cors_headers(request):
    """Get appropriate CORS headers based on the request origin."""
    origin = request.headers.get('Origin', '')
    cors_origin = origin if origin in ALLOWED_ORIGINS else 'https://campus-navigator.vercel.app'
    
    headers = {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS, GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }
    return headers

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - provides basic API info."""
    response = make_response(jsonify({
        'name': 'Campus Pathfinding API',
        'version': '1.0.0',
        'endpoints': ['/']
    }))
    response.headers.update(get_cors_headers(request))
    return response

@app.route('/', methods=['OPTIONS', 'POST'])
def find_path():
    """Handle POST requests to find a path and OPTIONS for CORS preflight."""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.update(get_cors_headers(request))
        return response, 204

    # Get CORS headers for all responses
    headers = get_cors_headers(request)
    
    # Handle non-POST methods
    if request.method != 'POST':
        response = make_response(jsonify({'error': 'Method not allowed'}))
        response.headers.update(headers)
        return response, 405

    # Parse request JSON
    data = request.get_json()
    if not data or 'start_lat' not in data or 'start_lng' not in data or 'end_lat' not in data or 'end_lng' not in data:
        response = make_response(jsonify({'error': 'Missing required fields: start_lat, start_lng, end_lat, end_lng'}))
        response.headers.update(headers)
        return response, 400
    
    start_lat = float(data['start_lat'])
    start_lng = float(data['start_lng'])
    end_lat = float(data['end_lat'])
    end_lng = float(data['end_lng'])
    
    # Optional custom padding parameter
    custom_padding = data.get('padding')
    if custom_padding is not None:
        try:
            custom_padding = int(custom_padding)
        except (ValueError, TypeError):
            # If padding is not a valid integer, ignore it
            custom_padding = None
    
    # Load grid config from Cloud Storage
    try:
        config = download_grid_config()
    except Exception as e:
        response = make_response(jsonify({'error': f'Failed to load grid config: {str(e)}'}))
        response.headers.update(headers)
        return response, 500
    
    # Convert lat-long to grid coordinates
    start_row, start_col = lat_lng_to_grid(start_lat, start_lng, config)
    end_row, end_col = lat_lng_to_grid(end_lat, end_lng, config)
    
    # Validate coordinates
    adjustments = {}
    
    # Check if start point is within grid bounds
    if not (0 <= start_row < config['rows'] and 0 <= start_col < config['cols']):
        # Find nearest valid point within grid
        start_row = max(0, min(start_row, config['rows'] - 1))
        start_col = max(0, min(start_col, config['cols'] - 1))
        adjustments['start_point'] = 'moved inside grid bounds'
    
    # Check if end point is within grid bounds
    if not (0 <= end_row < config['rows'] and 0 <= end_col < config['cols']):
        # Find nearest valid point within grid
        end_row = max(0, min(end_row, config['rows'] - 1))
        end_col = max(0, min(end_col, config['cols'] - 1))
        adjustments['end_point'] = 'moved inside grid bounds'
    
    # Get the grid data from config
    grid = config['grid']
    
    # Check if start or end points are on obstacles
    if grid[start_row][start_col] == 1:
        new_start_row, new_start_col = find_nearest_valid_point(grid, start_row, start_col, config['rows'], config['cols'])
        if new_start_row is not None and new_start_col is not None:
            start_row, start_col = new_start_row, new_start_col
            adjustments['start_point'] = 'moved to nearest valid point'
        else:
            response = make_response(jsonify({'error': 'Start point is on an obstacle and no valid nearby point found'}))
            response.headers.update(headers)
            return response, 400
    
    if grid[end_row][end_col] == 1:
        new_end_row, new_end_col = find_nearest_valid_point(grid, end_row, end_col, config['rows'], config['cols'])
        if new_end_row is not None and new_end_col is not None:
            end_row, end_col = new_end_row, new_end_col
            adjustments['end_point'] = 'moved to nearest valid point'
        else:
            response = make_response(jsonify({'error': 'End point is on an obstacle and no valid nearby point found'}))
            response.headers.update(headers)
            return response, 400
    
    # Apply A* pathfinding algorithm
    path_grid = a_star(grid, (start_row, start_col), (end_row, end_col), custom_padding)
    
    if not path_grid:
        response = make_response(jsonify({'error': 'No path found between the specified points'}))
        response.headers.update(headers)
        return response, 404
    
    # Convert grid path to lat-long coordinates
    path_lat_lng = [grid_to_lat_lng(row, col, config) for row, col in path_grid]
    
    # Prepare response
    result = {
        'path': path_lat_lng
    }
    
    # Include adjustment information if any adjustments were made
    if adjustments:
        result['adjustments'] = adjustments
    
    response = make_response(jsonify(result))
    response.headers.update(headers)
    return response
