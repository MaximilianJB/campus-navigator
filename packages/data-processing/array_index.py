import json
import os
import numpy as np

def process_grid_arrays(filename="grid_storage.json"):
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    # Load the grid data
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            grid_data = json.load(file)
        print(f"Successfully loaded {filename}")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return

    # Process each grid array in the data
    array_index = 0  # To track which array we're processing

    for grid_name, grid in grid_data.items():
        # Skip commented out files (assuming they're prefixed with //)
        if grid_name.startswith('//'):
            continue
            
        # Convert to numpy array for easier manipulation
        grid_array = np.array(grid)
        
        # Find non-zero elements
        non_zero_mask = grid_array != 0
        
        if np.any(non_zero_mask):
            if array_index == 0:
                # First array keeps its original 0s and 1s
                print(f"Processed {grid_name}: kept original 0s and 1s")
            else:
                # Subsequent arrays get their index value
                grid_array[non_zero_mask] = array_index + 1
                print(f"Processed {grid_name}: assigned value {array_index + 1} to non-zero elements")
            
            # Update the original grid data
            grid_data[grid_name] = grid_array.tolist()
        else:
            print(f"Processed {grid_name}: no non-zero values found")
        
        array_index += 1

    # Save the modified data back to the original file
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(grid_data, file, indent=4)
        print(f"Successfully updated original file {file_path}")
    except Exception as e:
        print(f"Error saving updated grid: {str(e)}")

    return grid_data

def main():
    # Process the grid arrays
    processed_grids = process_grid_arrays()
    
    if processed_grids:
        # Print some statistics
        print("\nProcessing Summary:")
        for filename, grid in processed_grids.items():
            if filename.startswith('//'):
                continue
            grid_array = np.array(grid)
            non_zero_count = np.sum(grid_array != 0)
            unique_values = np.unique(grid_array[grid_array != 0])
            values_str = ", ".join(map(str, unique_values)) if len(unique_values) > 0 else "none"
            print(f"{filename}: {non_zero_count} non-zero values, values used: {values_str}")

if __name__ == "__main__":
    main()