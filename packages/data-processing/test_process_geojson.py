import os
import json
import numpy as np
from process_geojson import GeoJSONGridProcessor

def test_grid_processing():
    # Initialize processor - this will automatically load and process the base grid
    processor = GeoJSONGridProcessor()
    
    # Get the base grid
    base_grid = processor.generated_grid
    print(f"\nBase grid shape: {base_grid.shape}")
    print(f"Number of building cells: {np.sum(base_grid == 1)}")
    
    # Process entrances
    entrance_grid = processor.process_entrances()
    if entrance_grid is not None:
        print("\nEntrance processing results:")
        entrance_points = np.where(entrance_grid == 1)
        print(f"Found {len(entrance_points[0])} entrance points")
        
        # Validate entrance positions
        valid_entrances = 0
        for i in range(len(entrance_points[0])):
            row, col = entrance_points[0][i], entrance_points[1][i]
            # Check if entrance is on a building edge
            is_edge = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    new_row, new_col = row + dx, col + dy
                    if (0 <= new_row < base_grid.shape[0] and 
                        0 <= new_col < base_grid.shape[1] and 
                        base_grid[new_row, new_col] == 0):
                        is_edge = True
                        break
                if is_edge:
                    break
            
            if is_edge and base_grid[row, col] == 1:
                valid_entrances += 1
            else:
                print(f"Warning: Invalid entrance at ({row}, {col})")
                
        print(f"Valid entrances: {valid_entrances}/{len(entrance_points[0])}")
    
    # Process hallways
    hallway_grid = processor.process_hallways()
    if hallway_grid is not None:
        print("\nHallway processing results:")
        hallway_points = np.where(hallway_grid == 1)
        print(f"Found {len(hallway_points[0])} hallway points")
        
        # Validate hallway positions
        valid_hallways = 0
        for i in range(len(hallway_points[0])):
            row, col = hallway_points[0][i], hallway_points[1][i]
            # Check if hallway is inside building (not on edge)
            is_valid = True
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    new_row, new_col = row + dx, col + dy
                    if (0 <= new_row < base_grid.shape[0] and 
                        0 <= new_col < base_grid.shape[1] and 
                        base_grid[new_row, new_col] == 0):
                        is_valid = False
                        break
                if not is_valid:
                    break
            
            if is_valid and base_grid[row, col] == 1:
                valid_hallways += 1
            else:
                print(f"Warning: Invalid hallway point at ({row}, {col})")
                
        print(f"Valid hallway points: {valid_hallways}/{len(hallway_points[0])}")
    
    # Save the results
    save_path = os.path.join(os.path.dirname(__file__), "grid_storage.json")
    data = {
        "campus1.geojson": base_grid.tolist(),
        "entrances.geojson": entrance_grid.tolist() if entrance_grid is not None else [],
        "hallways.geojson": hallway_grid.tolist() if hallway_grid is not None else []
    }
    
    with open(save_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nSaved processed grids to {save_path}")

if __name__ == "__main__":
    test_grid_processing()
