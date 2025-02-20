import json
import geopandas as gpd
import math

# Constants
GRID_SQUARE_SIZE = 2 # meters (2x2 meters)

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def read_geojson_file(file_path):
    data = gpd.read_file(file_path)
    return data

def lat_meters_to_degrees(meters):
    return meters / 111320  # Approximate conversion for latitude

def lon_meters_to_degrees(meters, latitude):
    return meters / (111320 * math.cos(math.radians(latitude)))  # Adjust for longitude

if __name__ == "__main__":
    json_file_path = 'packages/data-processing/grid_storage.json'
    geojson_file_path = 'packages/data-processing/campus_square.geojson'

    # store the grid array in a variable
    grid_json = read_json_file(json_file_path)
    grid_array = grid_json['campus1.geojson']
    
    # store metrics about the geojson file in a variable
    geojson_square = read_geojson_file(geojson_file_path)
    # Extract the coordinates of the polygon
    polygon = geojson_square.geometry.iloc[0]
    coordinates = polygon.exterior.coords[:-1]

    # Extract latitude and longitude values
    lats = [coord[1] for coord in coordinates]
    lngs = [coord[0] for coord in coordinates]

    # Calculate the latitude and longitude range
    grid_min_lat = min(lats)
    grid_max_lat = max(lats)
    grid_min_lng = min(lngs)
    grid_max_lng = max(lngs)

    # Compute number of rows and columns
    grid_num_rows = int((grid_max_lat - grid_min_lat) / lat_meters_to_degrees(GRID_SQUARE_SIZE))
    grid_num_cols = int((grid_max_lng - grid_min_lng) / lon_meters_to_degrees(GRID_SQUARE_SIZE, (grid_min_lat + grid_max_lat) / 2))
    
    # build new json object
    new_json = {
        "rows": grid_num_rows,
        "cols": grid_num_cols,
        "lat_min": grid_min_lat,
        "lat_max": grid_max_lat,
        "lng_min": grid_min_lng,
        "lng_max": grid_max_lng,
        "grid": grid_array,
    }
    
    # write new json object to file
    with open('packages/data-processing/grid_config.json', 'w') as file:
        json.dump(new_json, file)
