# Goal of this file is the following:
# - Process geojson files
# - Define our grid metrics (tommy's work)
# - Define function to convert lat/long to grid coordinates
import json
import geopy.distance
import os
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, shape
from rasterio.features import rasterize
from affine import Affine
from pyproj import Transformer

class GeoJSONGridProcessor:
    saved_grids = {}  # Dictionary to store generated grids

    def __init__(self, geojson_filename="campus1.geojson", cell_size=2):
        # Get the directory of the current script (process_geojson.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.geojson_path = os.path.join(script_dir, geojson_filename)
        self.cell_size = cell_size
        self.geojson_filename = geojson_filename  # Store filename for indexing
        self.load_geojson()

        # Convert lat/lon to UTM for accurate grid mapping
        self.transformer = Transformer.from_crs("epsg:4326", "epsg:32611", always_xy=True)
        self.ZERO_POINT = self.latlon_to_utm(47.6619, -117.4095)  
        self.END_POINT = self.latlon_to_utm(47.6706, -117.3967)  
        self.GRID_SIZE = (int((self.END_POINT[1] - self.ZERO_POINT[1]) / self.cell_size),
                             int((self.END_POINT[0] - self.ZERO_POINT[0]) / self.cell_size))
        self.generated_grid = self.generate_grid()
        
        # Save grid, overwrite grid1 if the same GeoJSON is used
        grid_name = "grid1" if geojson_filename == "campus1.geojson" else f"grid_{geojson_filename.split('.')[0]}"
        GeoJSONGridProcessor.saved_grids[grid_name] = self.generated_grid
        
        # Print out the generated grid array
        print(f"{grid_name} generated successfully!")
        np.set_printoptions(threshold=np.inf)
        print(self.generated_grid)
        
    def latlon_to_utm(self, lat, lon):
        return self.transformer.transform(lon, lat)

    def load_geojson(self):
        try:
            with open(self.geojson_path, "r", encoding="utf-8") as file:
                self.geojson_data = json.load(file)
            print("Successfully loaded GeoJSON!")
        except FileNotFoundError:
            print(f"Error: GeoJSON file not found at {self.geojson_path}")
            self.geojson_data = None

    def calculate_grid_size(self):
        lat_range_meters = geopy.distance.distance((self.ZERO_POINT[1], self.ZERO_POINT[0]),
                                                   (self.END_POINT[1], self.ZERO_POINT[0])).m
        lon_range_meters = geopy.distance.distance((self.ZERO_POINT[1], self.ZERO_POINT[0]),
                                                   (self.ZERO_POINT[1], self.END_POINT[0])).m
        return int(lat_range_meters // self.cell_size), int(lon_range_meters // self.cell_size)

    def generate_grid(self):
        if not self.geojson_data:
            print("GeoJSON data is empty or not loaded.")
            return np.zeros(self.GRID_SIZE, dtype=int)

        # Extract obstacle polygons, including MultiPolygons
        obstacle_polygons = []
        transformer = Transformer.from_crs("epsg:4326", "epsg:32611", always_xy=True)
        for feature in self.geojson_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type == "Polygon":
                utm_poly = Polygon([transformer.transform(lon, lat) for lon, lat in geom.exterior.coords])
                obstacle_polygons.append(utm_poly)
                obstacle_polygons.append(geom)
            elif geom.geom_type == "MultiPolygon":
                utm_multipoly = MultiPolygon([
                    Polygon([transformer.transform(lon, lat) for lon, lat in poly.exterior.coords])
                    for poly in geom.geoms
                ])
                obstacle_polygons.extend(list(utm_multipoly.geoms))
                obstacle_polygons.extend(list(geom.geoms))  # Flatten MultiPolygon

        if not obstacle_polygons:
            print("Warning: No valid obstacle polygons found in GeoJSON.")
            return np.zeros(self.GRID_SIZE, dtype=int)

        # Print bounding boxes for debugging
        print("Extracted obstacle polygons with bounding boxes:")
        for poly in obstacle_polygons:
            print(f" - {poly.bounds}")

        # Correct affine transformation for rasterization
        x_res = (self.END_POINT[0] - self.ZERO_POINT[0]) / self.GRID_SIZE[1]
        y_res = (self.END_POINT[1] - self.ZERO_POINT[1]) / self.GRID_SIZE[0]
        transform = Affine.translation(self.ZERO_POINT[0], self.END_POINT[1]) * Affine.scale(x_res, -y_res)

        # Rasterize polygons onto the grid
        grid = rasterize(
            [(poly, 1) for poly in obstacle_polygons],
            out_shape=self.GRID_SIZE,
            transform=transform,
            fill=0,
            all_touched=True  # Ensures all touched cells are considered obstacles
        )

        print("Grid generated successfully with obstacles!")
        print("Obstacle cells in grid (1s indicate obstacles):")
        # Print only obstacle cell coordinates instead of full grid
        obstacle_indices = np.argwhere(grid == 1)
        print(f"Obstacle cells (coordinates of 1s):", obstacle_indices)

        # return grid

# Create an instance of the processor to be used in grid_canvas.py
geojson_processor = GeoJSONGridProcessor()

def get_grid():
    return geojson_processor.generated_grid

def get_grid_size():
    return geojson_processor.GRID_SIZE

def get_saved_grids():
    return GeoJSONGridProcessor.saved_grids
