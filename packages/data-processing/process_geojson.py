import json
import os
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from rasterio.features import rasterize
from affine import Affine
from pyproj import Transformer
from grid_utils import GridUtils

class GeoJSONGridProcessor:
    def __init__(self, geojson_filename="campus_detailed_2.24.geojson", cell_size=2):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.geojson_path = os.path.join(script_dir, geojson_filename)
        self.cell_size = cell_size
        self.geojson_filename = geojson_filename  
        self.load_geojson()

        # Convert lat/lon to UTM for accurate grid mapping
        self.transformer = Transformer.from_crs("epsg:4326", "epsg:32611", always_xy=True)
        # Expand the bounding box slightly to ensure we capture all features
        self.ZERO_POINT = self.latlon_to_utm(47.6615, -117.4100)  # Slightly SW
        self.END_POINT = self.latlon_to_utm(47.6710, -117.3962)   # Slightly NE
        
        # Calculate grid dimensions
        utm_width = self.END_POINT[0] - self.ZERO_POINT[0]
        utm_height = self.END_POINT[1] - self.ZERO_POINT[1]
        
        # Ensure cell_size is in UTM units (meters)
        self.utm_cell_size = 2.0  # 2 meters per cell
        
        self.GRID_SIZE = (
            int(utm_height / self.utm_cell_size),
            int(utm_width / self.utm_cell_size)
        )
        
        print(f"Grid dimensions: {self.GRID_SIZE}")
        print(f"UTM bounds: ({self.ZERO_POINT}, {self.END_POINT})")
        
        self.generated_grid = self.generate_grid()
        if self.generated_grid is not None and np.any(self.generated_grid == 1):
            self.save_grid()
        else:
            print("Error: Grid generation failed or contains no obstacles, not saving.")

    def latlon_to_utm(self, lat, lon):
        return self.transformer.transform(lon, lat)

    def utm_to_grid_coords(self, x, y):
        """Convert UTM coordinates to grid coordinates"""
        # Calculate relative position in UTM space
        rel_x = x - self.ZERO_POINT[0]
        rel_y = self.END_POINT[1] - y  # Flip Y axis
        
        # Convert to grid coordinates
        col = int(rel_x / self.utm_cell_size)
        row = int(rel_y / self.utm_cell_size)
        
        return row, col

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

    def process_entrances(self, entrances_geojson="entrances.geojson"):
        entrances_path = os.path.join(os.path.dirname(__file__), entrances_geojson)
        try:
            with open(entrances_path, "r", encoding="utf-8") as file:
                entrances_data = json.load(file)
            print("Successfully loaded Entrances GeoJSON!")
        except FileNotFoundError:
            print(f"Error: Entrances GeoJSON file not found at {entrances_path}")
            return

        # Initialize grid utils
        grid_utils = GridUtils(self.utm_cell_size, self.generated_grid)
        entrance_points = []

        for feature in entrances_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type == "Point":
                # Convert to UTM
                utm_x, utm_y = self.latlon_to_utm(geom.y, geom.x)
                
                # Convert to grid coordinates
                grid_row, grid_col = self.utm_to_grid_coords(utm_x, utm_y)
                
                # Ensure coordinates are within grid bounds
                if (0 <= grid_row < self.GRID_SIZE[0] and 
                    0 <= grid_col < self.GRID_SIZE[1]):
                    # Check if this point is on a building edge
                    if grid_utils.is_on_building_edge(grid_row, grid_col):
                        # Add a 3x3 grid of entrance points for better traversability
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                new_row, new_col = grid_row + dr, grid_col + dc
                                if (0 <= new_row < self.GRID_SIZE[0] and 
                                    0 <= new_col < self.GRID_SIZE[1] and
                                    not (dr == 0 and dc == 0 and self.generated_grid[new_row, new_col] == 1)):  # Don't overwrite center building tile
                                    entrance_points.append((new_row, new_col))

        # Create entrance grid
        entrance_grid = np.zeros_like(self.generated_grid)
        for row, col in entrance_points:
            if self.generated_grid[row, col] != 1:  # Don't overwrite buildings
                entrance_grid[row, col] = 1
        
        print(f"Processed {len(set(entrance_points))} entrance points")
        return entrance_grid

    def process_hallways(self, hallways_geojson="hallways.geojson"):
        hallways_path = os.path.join(os.path.dirname(__file__), hallways_geojson)
        try:
            with open(hallways_path, "r", encoding="utf-8") as file:
                hallways_data = json.load(file)
            print("Successfully loaded Hallways GeoJSON!")
        except FileNotFoundError:
            print(f"Error: Hallways GeoJSON file not found at {hallways_path}")
            return

        # Initialize grid utils and get entrance points
        grid_utils = GridUtils(self.utm_cell_size, self.generated_grid)
        entrance_grid = self.process_entrances()  # Get entrance points first
        hallway_points = []

        for feature in hallways_data["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type == "LineString":
                # Convert all coordinates to UTM
                utm_coords = [
                    self.latlon_to_utm(lat, lon) 
                    for lon, lat in geom.coords
                ]
                
                # Convert to grid coordinates
                grid_coords = [
                    self.utm_to_grid_coords(x, y)
                    for x, y in utm_coords
                ]
                
                # Process each segment of the hallway
                for i in range(len(grid_coords) - 1):
                    start = grid_coords[i]
                    end = grid_coords[i + 1]
                    
                    # Use Bresenham's line algorithm to get all points along the line
                    line_points = grid_utils._bresenham_line(
                        start[0], start[1], 
                        end[0], end[1]
                    )
                    
                    # Add points with a minimum width of 3 tiles
                    for row, col in line_points:
                        if (0 <= row < self.GRID_SIZE[0] and 
                            0 <= col < self.GRID_SIZE[1]):
                            # Add center point and neighbors in a cross pattern (+)
                            for dr, dc in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                                new_row, new_col = row + dr, col + dc
                                if (0 <= new_row < self.GRID_SIZE[0] and 
                                    0 <= new_col < self.GRID_SIZE[1]):
                                    # Allow hallways to override buildings but not entrances
                                    if entrance_grid[new_row, new_col] != 1:
                                        hallway_points.append((new_row, new_col))

        # Create hallway grid
        hallway_grid = np.zeros_like(self.generated_grid)
        for row, col in hallway_points:
            if entrance_grid[row, col] != 1:  # Only check for entrances, allow overriding buildings
                hallway_grid[row, col] = 1
        
        print(f"Processed {len(set(hallway_points))} hallway points")
        return hallway_grid

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
