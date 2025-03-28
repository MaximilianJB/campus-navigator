import numpy as np
from shapely.geometry import Point, LineString, shape
from typing import List, Tuple, Dict, Any

class GridUtils:
    def __init__(self, grid_size: float, base_grid: np.ndarray):
        """
        Initialize GridUtils with grid parameters
        
        Args:
            grid_size: Size of each grid unit
            base_grid: The base building grid (0 for empty, 1 for building)
        """
        self.grid_size = grid_size
        self.base_grid = base_grid
        
    def is_on_building_edge(self, row: int, col: int) -> bool:
        """
        Check if a grid position is on the edge of a building
        
        Args:
            row: Grid row index
            col: Grid column index
            
        Returns:
            bool: True if position is on building edge
        """
        if self.base_grid[row, col] != 1:
            return False
            
        # Check all 8 adjacent cells
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                    
                new_row, new_col = row + i, col + j
                if (0 <= new_row < self.base_grid.shape[0] and 
                    0 <= new_col < self.base_grid.shape[1] and 
                    self.base_grid[new_row, new_col] == 0):
                    return True
        return False
        
    def process_entrance(self, entrance_point: Point, utm_to_grid: callable) -> Tuple[int, int]:
        """
        Process an entrance point and ensure it's placed on building edge
        
        Args:
            entrance_point: Shapely Point object representing entrance
            utm_to_grid: Function to convert UTM coordinates to grid indices
            
        Returns:
            Tuple[int, int]: Grid coordinates for the entrance
        """
        # Convert entrance point to grid coordinates
        grid_row, grid_col = utm_to_grid(entrance_point.x, entrance_point.y)
        
        # If not on building edge, find nearest edge
        if not self.is_on_building_edge(grid_row, grid_col):
            best_dist = float('inf')
            best_pos = None
            
            # Search in a 5x5 grid around the point
            for i in range(max(0, grid_row - 2), min(self.base_grid.shape[0], grid_row + 3)):
                for j in range(max(0, grid_col - 2), min(self.base_grid.shape[1], grid_col + 3)):
                    if self.is_on_building_edge(i, j):
                        dist = abs(i - grid_row) + abs(j - grid_col)
                        if dist < best_dist:
                            best_dist = dist
                            best_pos = (i, j)
            
            if best_pos:
                grid_row, grid_col = best_pos
            else:
                raise ValueError(f"No valid building edge found near entrance at ({grid_row}, {grid_col})")
                
        return grid_row, grid_col
        
    def is_valid_hallway_position(self, row: int, col: int) -> bool:
        """
        Check if a position is valid for a hallway
        
        Args:
            row: Grid row index
            col: Grid column index
            
        Returns:
            bool: True if position is valid for hallway
        """
        # Must be on building (black tile)
        if self.base_grid[row, col] != 1:
            return False
            
        # Must not be adjacent to empty space (white tile)
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                    
                new_row, new_col = row + i, col + j
                if (0 <= new_row < self.base_grid.shape[0] and 
                    0 <= new_col < self.base_grid.shape[1] and 
                    self.base_grid[new_row, new_col] == 0):
                    return False
        return True
        
    def process_hallway(self, hallway_line: LineString, utm_to_grid: callable) -> List[Tuple[int, int]]:
        """
        Process a hallway line and ensure it's placed properly within building
        
        Args:
            hallway_line: Shapely LineString object representing hallway
            utm_to_grid: Function to convert UTM coordinates to grid indices
            
        Returns:
            List[Tuple[int, int]]: List of grid coordinates for the hallway
        """
        hallway_points = []
        
        # Convert line coordinates to grid coordinates
        coords = [(utm_to_grid(x, y)) for x, y in hallway_line.coords]
        
        # Use Bresenham's line algorithm to get all grid cells between points
        for i in range(len(coords) - 1):
            start_row, start_col = coords[i]
            end_row, end_col = coords[i + 1]
            
            # Get all points along the line
            line_points = self._bresenham_line(start_row, start_col, end_row, end_col)
            
            # Filter points to ensure they're valid hallway positions
            valid_points = [
                (row, col) for row, col in line_points 
                if (0 <= row < self.base_grid.shape[0] and 
                    0 <= col < self.base_grid.shape[1] and 
                    self.is_valid_hallway_position(row, col))
            ]
            
            hallway_points.extend(valid_points)
            
        return list(set(hallway_points))  # Remove duplicates
        
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        """
        Implementation of Bresenham's line algorithm
        
        Args:
            x0, y0: Starting coordinates
            x1, y1: Ending coordinates
            
        Returns:
            List[Tuple[int, int]]: List of coordinates along the line
        """
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
                
        points.append((x, y))
        return points
