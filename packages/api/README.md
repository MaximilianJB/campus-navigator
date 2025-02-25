# Pathfinding API

This directory contains the API for calculating the shortest path between two geographical coordinates using the **A\*** pathfinding algorithm. The API is hosted on **Google Cloud Run** and exposes a single endpoint for path calculations.

## Files Overview

### `main.py`
- Implements the API using a web framework (e.g., FastAPI or Flask).
- Accepts **POST** requests with JSON payloads.
- Processes start and end latitude/longitude coordinates.
- Returns the **shortest path** as a list of coordinates.

### `Dockerfile`
- Defines the containerization setup for deploying the API.
- Specifies dependencies and the execution environment for Google Cloud Run.

## API Usage

### Endpoint
`POST https://calculatecampuspath-842151361761.us-central1.run.app`

### Request Format
The API accepts a **JSON payload** with the following fields:

| Field       | Type   | Description                                  |
|------------|-------|----------------------------------------------|
| `start_lat` | float | Latitude of the starting point.            |
| `start_lng` | float | Longitude of the starting point.           |
| `end_lat`   | float | Latitude of the destination point.         |
| `end_lng`   | float | Longitude of the destination point.        |

### Example Request (cURL)
```sh
curl -X POST -H "Content-Type: application/json" \
     -d '{"start_lat": 47.6625, "start_lng": -117.4090, "end_lat": 47.6700, "end_lng": -117.3970}' \
     https://calculatecampuspath-842151361761.us-central1.run.app
```

### Response Format
The response contains a **list of latitude/longitude coordinates** representing the shortest path.
```json
{
  "path": [
    [47.66249194241168,-117.40901253340753],
    [47.66249194241168,-117.40898582469885],
    [47.66249194241168,-117.40895911599014]
  ]
}
```

## Deployment
- The API is containerized using **Docker**
- Hosted on **Google Cloud Run** for scalability and serverless execution

## Running Locally
1. Navigate to the `/api` directory
2. Build the Docker image
    `docker build -t calculatecampuspath:test .`
3. Run the container
    `docker run -p 8080:8080 -e PORT=8080 calculatecampuspath:test`
4. Send request to local server
    ```sh
    curl -X POST -H "Content-Type: application/json" \
        -d '{"start_lat": 47.6625, "start_lng": -117.4090, "end_lat": 47.6700, "end_lng": -117.3970}' \
        http://localhost:8080
    ```
