"""
Flask application for processing GeoJSON building entrances
"""
import json
import io
from flask import Flask, request, make_response, jsonify
from src.utils import process_geojson_entrances
from src.storage import upload_to_gcs, DEFAULT_BUCKET_NAME

app = Flask(__name__)

# Define allowed origins for CORS
ALLOWED_ORIGINS = ['http://localhost:3000', 'https://campus-navigator.vercel.app']

def get_cors_headers(request):
    """Get appropriate CORS headers based on the request origin."""
    origin = request.headers.get('Origin', '')
    cors_origin = origin if origin in ALLOWED_ORIGINS else 'https://campus-navigator.vercel.app'
    
    headers = {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }
    return headers

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - provides basic API info."""
    response = make_response(jsonify({
        'name': 'Building Entrances Processing API',
        'version': '1.0.0',
        'endpoints': ['/process-entrances']
    }))
    return response

@app.route('/process-entrances', methods=['OPTIONS', 'POST'])
def process_entrances():
    """Handle POST requests to process GeoJSON and label entrances.
    
    Expects:
    - multipart/form-data with:
      - geojson_file: The GeoJSON file to process
      - title: A string identifier used to name the subfolder in GCS
      
    Returns:
    - JSON response with status, message, file path, and public URL
    """
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.update(get_cors_headers(request))
        return response, 204

    # Add CORS headers to all responses
    headers = get_cors_headers(request)
    
    try:
        # Check if request contains multipart form data
        if 'geojson_file' not in request.files:
            response = make_response(jsonify({'error': 'No geojson_file in request'}))
            response.headers.update(headers)
            return response, 400
        
        geojson_file = request.files['geojson_file']
        title = request.form.get('title', 'untitled')
        
        # Validate title (basic sanitization)
        if not title or not title.replace('-', '').replace('_', '').isalnum():
            title = 'untitled'
        
        # Read the GeoJSON file
        geojson_content = geojson_file.read()
        try:
            geojson_data = json.loads(geojson_content)
        except json.JSONDecodeError:
            response = make_response(jsonify({'error': 'Invalid GeoJSON format'}))
            response.headers.update(headers)
            return response, 400
        
        # Process the GeoJSON to label entrances
        labeled_entrances = process_geojson_entrances(geojson_data)
        
        # Upload to Google Cloud Storage
        upload_path = f"{title}/entrances.json"
        public_url = upload_to_gcs(labeled_entrances, DEFAULT_BUCKET_NAME, upload_path)
        
        # Return success response with public URL
        result = {
            'status': 'success',
            'message': f'Successfully processed {len(labeled_entrances)} entrances',
            'file_path': upload_path,
            'public_url': public_url
        }
        
        response = make_response(jsonify(result))
        response.headers.update(headers)
        return response, 200
        
    except Exception as e:
        response = make_response(jsonify({'error': f'Error processing request: {str(e)}'}))
        response.headers.update(headers)
        return response, 500
