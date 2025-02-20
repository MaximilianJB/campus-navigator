import folium
import requests

# API endpoint
url = "https://calculatecampuspath-842151361761.us-central1.run.app"

# Request payload
data = {
    "start_lat": 47.6625,
    "start_lng": -117.4090,
    "end_lat": 47.6700,
    "end_lng": -117.3970
}

# Send the POST request
response = requests.post(url, json=data)

# Check if the request was successful
if response.status_code == 200:
    result = response.json()

    # Print response to understand the structure
    print("API Response:", result)

    # Extract the "path" attribute
    path = result.get("path", [])

    if path and isinstance(path[0], list) and len(path[0]) == 2:
        # Create a folium map centered at the starting point
        start_point = path[0]  # First coordinate pair (lat, lng)
        m = folium.Map(location=start_point, zoom_start=15)

        # Add markers for start and end points
        folium.Marker(
            path[0], popup="Start", icon=folium.Icon(color="green")
        ).add_to(m)
        
        folium.Marker(
            path[-1], popup="End", icon=folium.Icon(color="red")
        ).add_to(m)

        # Add a polyline to the map
        folium.PolyLine(path, color="blue", weight=5, opacity=0.7).add_to(m)

        # Save and display map
        m.save("map.html")
        print("Map has been saved as map.html. Open it in your browser.")
    
    else:
        print("Error: No valid path data received from the API.")
else:
    print(f"API request failed with status code {response.status_code}: {response.text}")