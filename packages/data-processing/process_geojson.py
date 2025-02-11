import json
import os
import numpy as np
import geopy.distance
from shapely.geometry import Polygon, MultiPolygon, shape
from rasterio.features import rasterize
from affine import Affine
from pyproj import Transformer

class GeoJSONGridProcessor:
    def __init__(self, geojson_filename="campus1.geojson", cell_size=2):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.geojson_path = os.path.join(script_dir, geojson_filename)
        self.cell_size = cell_size
        self.geojson_filename = geojson_filename  
        self.load_geojson()

        # Convert lat/lon to UTM for accurate grid mapping
        self.transformer = Transformer.from_crs("epsg:4326", "epsg:32611", always_xy=True)
        self.ZERO_POINT = self.latlon_to_utm(47.6619, -117.4095)
        self.END_POINT = self.latlon_to_utm(47.6706, -117.3967)
        self.GRID_SIZE = (int((self.END_POINT[1] - self.ZERO_POINT[1]) / self.cell_size),
                             int((self.END_POINT[0] - self.ZERO_POINT[0]) / self.cell_size))

        self.generated_grid = self.generate_grid()
        if self.generated_grid is not None and np.any(self.generated_grid == 1):
            self.save_grid()
        else:
            print("Error: Grid generation failed or contains no obstacles, not saving.")

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

    def generate_grid(self):
        if not self.geojson_data:
            print("GeoJSON data is empty or not loaded.")
            return np.zeros(self.GRID_SIZE, dtype=int)

        obstacle_polygons = []
        for feature in self.geojson_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type == "Polygon":
                obstacle_polygons.append(geom)
            elif geom.geom_type == "MultiPolygon":
                obstacle_polygons.extend(geom.geoms)

        if not obstacle_polygons:
            print("Warning: No valid obstacle polygons found in GeoJSON.")
            return np.zeros(self.GRID_SIZE, dtype=int)

        print("Extracted obstacle polygons (converted to UTM):")
        transformed_polygons = []
        for poly in obstacle_polygons:
            transformed_poly = Polygon([self.latlon_to_utm(lat, lon) for lon, lat in poly.exterior.coords])
            transformed_polygons.append(transformed_poly)
            print(f" - Bounding Box: {transformed_poly.bounds}")

        x_res = (self.END_POINT[0] - self.ZERO_POINT[0]) / self.GRID_SIZE[1]
        y_res = (self.END_POINT[1] - self.ZERO_POINT[1]) / self.GRID_SIZE[0]
        transform = Affine.translation(self.ZERO_POINT[0], self.END_POINT[1]) * Affine.scale(x_res, -y_res)

        grid = rasterize(
            [(poly, 1) for poly in transformed_polygons],
            out_shape=self.GRID_SIZE,
            transform=transform,
            fill=0,
            all_touched=True 
        )

        obstacle_cells = np.column_stack(np.where(grid == 1))
        if obstacle_cells.size == 0:
            print("Error: No obstacle cells detected after rasterization.")
        else:
            print("Obstacle cells (coordinates of 1s):", obstacle_cells)

        return grid if obstacle_cells.size > 0 else np.zeros(self.GRID_SIZE, dtype=int)

    def save_grid(self):
        grid_data = {self.geojson_filename: self.generated_grid.tolist()}
        save_path = os.path.join(os.path.dirname(__file__), "grid_storage.json")
        
        try:
            with open(save_path, "r", encoding="utf-8") as file:
                stored_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            stored_data = {}
        
        stored_data.update(grid_data)
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(stored_data, file, indent=4)
            print(f"Grid saved successfully to {save_path}")

geojson_processor = GeoJSONGridProcessor()

def get_grid():
    return geojson_processor.generated_grid

def get_grid_size():
    return geojson_processor.GRID_SIZE
