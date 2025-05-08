# Campus Pathfinding API

This API service calculates the shortest path between two geographical coordinates using the **A\*** pathfinding algorithm. The pathfinding is performed on a grid-based representation of the campus map.

## Features

- Accepts latitude/longitude coordinates for start and end points
- Uses A* algorithm for efficient path calculation
- Applies configurable obstacle padding for smoother paths
- Snaps points to valid non-obstacle locations when needed
- Returns paths as a series of geographical coordinates

## Project Structure

```
packages/api-pathfinding/
├── src/
│   ├── app.py         # Flask application and route handlers
│   ├── utils.py       # Pathfinding algorithms and coordinate utilities
│   └── storage.py     # Google Cloud Storage utilities
├── main.py            # Entry point for the application
├── requirements.txt   # Python dependencies
└── Dockerfile         # Container configuration for Cloud Run
```

## API Endpoints

### `GET /`

Returns basic information about the API.

### `POST /`

Calculates the shortest path between provided coordinates.

**Request:**
```json
{
  "start_lat": 47.6625,
  "start_lng": -117.4090,
  "end_lat": 47.6700,
  "end_lng": -117.3970,
  "padding": 2 // Optional custom padding value
}
```

**Response:**
```json
{
  "path": [
    [47.66249194241168, -117.40901253340753],
    [47.66249194241168, -117.40898582469885],
    [47.66249194241168, -117.40895911599014],
    ...
  ],
  "adjustments": {
    "start_point": "moved to nearest valid point" // Optional, included if adjustments were made
  }
}
```

## Error Responses

The API returns appropriate HTTP status codes and error messages:

- `400` - Missing required fields or invalid input
- `404` - No path found between the points
- `500` - Server error (e.g., failed to load grid configuration)

## Deployment to Google Cloud Run

1. Build the container:
   ```
   gcloud builds submit --tag gcr.io/PROJECT_ID/campus-pathfinding-api
   ```

2. Deploy to Cloud Run:
   ```
   gcloud run deploy campus-pathfinding-api \
     --image gcr.io/PROJECT_ID/campus-pathfinding-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
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

The application will be available at http://localhost:8080
