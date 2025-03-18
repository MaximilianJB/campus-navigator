import json
import os
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from rasterio.features import rasterize
from affine import Affine
from pyproj import Transformer

class GeoJSONGridProcessor:
    def __init__(self, geojson_filename="campus_detailed_2.24.geojson", cell_size=2):
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

    def process_entrances(self, entrance_geojson="entrances.geojson"):
        entrance_path = os.path.join(os.path.dirname(__file__), entrance_geojson)
        try:
            with open(entrance_path, "r", encoding="utf-8") as file:
                entrance_data = json.load(file)
            print("Successfully loaded Entrances GeoJSON!")
        except FileNotFoundError:
            print(f"Error: Entrances GeoJSON file not found at {entrance_path}")
            return

        entrance_polygons = []
        entrance_points = []

        for feature in entrance_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type in ["Polygon", "MultiPolygon"]:
                entrance_polygons.append(geom)
            elif geom.geom_type == "Point":
                entrance_points.append(geom)

        if not entrance_polygons and not entrance_points:
            print("Warning: No valid entrance features found in GeoJSON.")
            return

        # Rasterize polygon entrances (as filled areas)
        entrance_grid = rasterize(
        [(poly, 2) for poly in entrance_polygons],
            out_shape=self.GRID_SIZE,
            transform=Affine.translation(self.ZERO_POINT[0], self.END_POINT[1]) * Affine.scale(
                (self.END_POINT[0] - self.ZERO_POINT[0]) / self.GRID_SIZE[1],
                -(self.END_POINT[1] - self.ZERO_POINT[1]) / self.GRID_SIZE[0]
            ),
            fill=0,
            all_touched=True
        )

        # Convert entrance points to grid indices and mark them distinctly
        for point in entrance_points:
            x, y = self.latlon_to_utm(point.y, point.x)  # Convert lat/lon to UTM
            col = int((x - self.ZERO_POINT[0]) / self.cell_size)
            row = int((self.END_POINT[1] - y) / self.cell_size)

            if 0 <= row < self.GRID_SIZE[0] and 0 <= col < self.GRID_SIZE[1]:
                entrance_grid[row, col] = 3  # Mark entrance points distinctly

        # Save to grid_storage.json
        entrance_data = {entrance_geojson: entrance_grid.tolist()}
        save_path = os.path.join(os.path.dirname(__file__), "grid_storage.json")

        try:
            with open(save_path, "r", encoding="utf-8") as file:
                stored_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            stored_data = {}

        stored_data.update(entrance_data)
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(stored_data, file, indent=4)
            print(f"Entrance grid (including points) saved successfully to {save_path}")

        # Find and print all non-zero values in the entrance grid
        non_zero_cells = np.column_stack(np.where(entrance_grid > 0))
        if non_zero_cells.size == 0:
            print("Error: No entrance cells detected in the saved grid.")
        else:
            print("Entrance cells (coordinates of 2s and 3s):", non_zero_cells)

    def process_hallways(self, hallways_geojson="hallways.geojson", buffer_size=None):
        hallways_path = os.path.join(os.path.dirname(__file__), hallways_geojson)
        try:
            with open(hallways_path, "r", encoding="utf-8") as file:
                hallways_data = json.load(file)
            print("Successfully loaded Hallways GeoJSON!")
        except FileNotFoundError:
            print(f"Error: Hallways GeoJSON file not found at {hallways_path}")
            return

        hallway_lines = []
        for feature in hallways_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type == "LineString":
                hallway_lines.append(geom)

        if not hallway_lines:
            print("Warning: No valid hallway LineStrings found in GeoJSON.")
            return

        # Set default buffer size to at least the cell size
        buffer_size = buffer_size or self.cell_size

        # Convert hallways from lat/lon to UTM for accuracy
        buffered_hallways = [
            LineString([self.latlon_to_utm(lat, lon) for lon, lat in line.coords]).buffer(buffer_size, cap_style=2)
            for line in hallway_lines
        ]

        # Merge all buffered hallways
        hallway_union = unary_union(buffered_hallways)

        # Check if any hallway exists after buffering
        if hallway_union.is_empty:
            print("Error: No valid buffered hallways detected after transformation.")
            return

        print("Buffered Hallway Polygons Created!")
    
        # Rasterize the buffered hallways onto the grid
        hallway_grid = rasterize(
            [(hallway_union, 3)],  # Mark hallways distinctly with value 3
            out_shape=self.GRID_SIZE,
            transform=Affine.translation(self.ZERO_POINT[0], self.END_POINT[1]) * Affine.scale(
                (self.END_POINT[0] - self.ZERO_POINT[0]) / self.GRID_SIZE[1],
                -(self.END_POINT[1] - self.ZERO_POINT[1]) / self.GRID_SIZE[0]
            ),
            fill=0,
            all_touched=True  # Ensure that all touched cells are counted
        )

        # Check if rasterization worked
        non_zero_hallways = np.column_stack(np.where(hallway_grid == 3))
        if non_zero_hallways.size == 0:
            print("Error: No hallway cells detected after rasterization.")
        else:
            print("Hallway cells (coordinates of 3s):", non_zero_hallways)

        # Save hallways to grid_storage.json
        hallway_data = {hallways_geojson: hallway_grid.tolist()}
        save_path = os.path.join(os.path.dirname(__file__), "grid_storage.json")

        try:
            with open(save_path, "r", encoding="utf-8") as file:
                stored_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            stored_data = {}

        stored_data.update(hallway_data)
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(stored_data, file, indent=4)
            print(f"Hallway grid saved successfully to {save_path}")

        # **Check Entrances and Intersections**
        self.check_entrance_intersections(hallway_union)

    def check_entrance_intersections(self, hallway_union):
            """ Checks how many entrances exist and how many intersect with hallways. """
            entrance_path = os.path.join(os.path.dirname(__file__), "entrances.geojson")
            try:
                with open(entrance_path, "r", encoding="utf-8") as file:
                    entrance_data = json.load(file)
                print("Successfully loaded Entrances GeoJSON for intersection check!")
            except FileNotFoundError:
                print(f"Error: Entrances GeoJSON file not found at {entrance_path}")
                return

            entrance_points = []
            for feature in entrance_data["features"]:
                geom = shape(feature["geometry"])
                if geom.geom_type == "Point":
                    # Convert entrance lat/lon to UTM for correct intersection checking
                    utm_x, utm_y = self.latlon_to_utm(geom.y, geom.x)
                    entrance_points.append(Point(utm_x, utm_y))

            total_entrances = len(entrance_points)
            entrances_touching_hallways = sum(1 for pt in entrance_points if hallway_union.intersects(pt))

            print(f"Total entrances: {total_entrances}")
            print(f"Entrances connected to hallways: {entrances_touching_hallways}")

geojson_processor = GeoJSONGridProcessor()
geojson_processor.process_entrances()
geojson_processor.process_hallways()

def get_grid():
    return geojson_processor.generated_grid

def get_grid_size():
    return geojson_processor.GRID_SIZE
