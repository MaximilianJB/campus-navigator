# Building Entrances Processing API

This API service processes GeoJSON files containing building polygons and entrance points, labeling the entrances in a clockwise order from north, and stores the resulting JSON in Google Cloud Storage.

## Features

- Accepts GeoJSON files via a multipart/form-data POST request
- Processes entrance points by assigning them to buildings and labeling them in clockwise order
- Stores processed data in Google Cloud Storage
- Returns JSON responses with success/error information

## Project Structure

```
packages/api-entrances/
├── src/
│   ├── app.py         # Flask application and route handlers
│   ├── utils.py       # GeoJSON processing utilities
│   └── storage.py     # Google Cloud Storage utilities
├── main.py            # Entry point for the application
├── requirements.txt   # Python dependencies
└── Dockerfile         # Container configuration for Cloud Run
```

## API Endpoints

### `GET /`

Returns basic information about the API.

### `POST /process-entrances`

Processes a GeoJSON file to identify and label building entrances.

**Request:**
- Content-Type: `multipart/form-data`
- Parameters:
  - `geojson_file`: The GeoJSON file to process
  - `title`: String identifier for the subfolder in GCS where the result will be stored

**Response:**
```json
{
  "status": "success",
  "message": "Successfully processed X entrances",
  "file_path": "title/entrances.json",
  "public_url": "https://storage.googleapis.com/gu-campus-maps/title/entrances.json"
}
```

## Deployment to Google Cloud Run

1. Build the container:
   ```
   gcloud builds submit --tag gcr.io/PROJECT_ID/building-entrances-api
   ```

2. Deploy to Cloud Run:
   ```
   gcloud run deploy building-entrances-api --image gcr.io/PROJECT_ID/building-entrances-api
   ```

## Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

The application will be available at http://localhost:8081
