import json
import numpy as np
import matplotlib.pyplot as plt
from a_star import AStar
import os

# Global variables for interactive point selection
click_count = 0
start_point = None
end_point = None

def load_grid():
    """Load grid from grid_config.json."""
    grid_config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../data-processing/grid_config.json"
    )
    if not os.path.exists(grid_config_path):
        raise FileNotFoundError(f"grid_config.json not found at {grid_config_path}")
    with open(grid_config_path, "r") as f:
        grid_data = json.load(f)
    grid = np.array(grid_data["grid"], dtype=np.uint8)
    return grid

def visualize_grid(grid, path=None, smooth_path=None):
    """Visualize grid and paths."""
    plt.clf()  # Clear previous plot
    plt.imshow(grid, cmap='binary', origin='lower')  # 0=white, 1=black
    if path:
        path_x, path_y = zip(*path)
        plt.plot(path_x, path_y, 'b-', label='Raw Path', linewidth=1)
    if smooth_path:
        smooth_x, smooth_y = zip(*smooth_path)
        plt.plot(smooth_x, smooth_y, 'r-', label='Smoothed Path', linewidth=2)
    plt.legend()
    plt.title("Grid with A* Path (Click to set Start/End)")
    plt.xlabel("X (Columns)")
    plt.ylabel("Y (Rows)")
    plt.grid(False)
    plt.draw()

def on_click(event):
    """Handle mouse clicks to set start/end points."""
    global click_count, start_point, end_point
    if event.xdata is None or event.ydata is None:
        return
    # Convert click coordinates to grid indices
    ix = int(round(event.xdata))
    iy = int(round(event.ydata))
    if ix < 0 or ix >= grid.shape[1] or iy < 0 or iy >= grid.shape[0]:
        print(f"Click out of bounds: ({ix}, {iy})")
        return
    if grid[iy, ix] == 1:
        print(f"Invalid point: ({ix}, {iy}) is an obstacle")
        return
    if click_count == 0:
        start_point = (ix, iy)
        print(f"Start set: {start_point}")
        click_count += 1
    else:
        end_point = (ix, iy)
        print(f"End set: {end_point}")
        click_count = 0
        # Run A*
        astar = AStar(grid)
        path = astar.find_path(start_point, end_point)
        if path:
            smooth_path = astar.smooth_path(path)
            visualize_grid(grid, path, smooth_path)
        else:
            print("No path found")
            visualize_grid(grid)  # Redraw grid

if __name__ == "__main__":
    # Load grid
    try:
        grid = load_grid()
    except FileNotFoundError as e:
        print(e)
        exit(1)

    # Initialize plot
    fig = plt.figure(figsize=(10, 8))
    visualize_grid(grid)
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.savefig("grid.png")
    plt.show()

    # Optional: Hardcoded test for debugging
    """
    astar = AStar(grid)
    start = (10, 20)  # Adjust to valid grid = 0 coordinates
    end = (50, 60)
    path = astar.find_path(start, end)
    if path:
        smooth_path = astar.smooth_path(path)
        visualize_grid(grid, path, smooth_path)
        plt.show()
    else:
        print("No path found")
    """