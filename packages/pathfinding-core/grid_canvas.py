import tkinter as tk
import json
from a_star import a_star

# Constants
SQUARE_SIZE = 2

# Color scheme for different layers
LAYER_COLORS = {
    0: "white",      # Empty space
    1: "black",      # Buildings
    2: "red",        # Entrances
    3: "blue",       # Hallways
    4: "green",
    5: "purple",
    6: "orange",
    7: "brown",
    8: "pink",
    9: "cyan"
}

def read_json_file(file_path):
    """Read and return the grid data from grid_storage.json"""
    with open(file_path, "r") as file:
        return json.load(file)

class GridApp:
    def __init__(self, root, grid_data):
        self.root = root
        self.grid_data = grid_data
        self.cell_size = SQUARE_SIZE
        self.start = None
        self.end = None
        
        # Get grid dimensions from campus1.geojson
        self.base_grid = grid_data["campus1.geojson"]
        grid_height = len(self.base_grid)
        grid_width = len(self.base_grid[0])
        
        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas frame
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=grid_width * self.cell_size,
            height=grid_height * self.cell_size
        )
        self.canvas.pack()
        
        # Create legend frame
        self.legend_frame = tk.Frame(self.main_frame, width=200)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.create_legend()
        
        self.draw_grid()
        self.canvas.bind("<Button-1>", self.set_start)
        self.canvas.bind("<Button-3>", self.set_end)

    def create_legend(self):
        """Creates a legend showing what each color represents"""
        tk.Label(self.legend_frame, text="Legend:", font=('Arial', 10, 'bold')).pack(pady=5)
        
        labels = {
            1: "Buildings",
            2: "Entrances",
            3: "Hallways"
        }
        
        for value, label in labels.items():
            frame = tk.Frame(self.legend_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Color sample
            sample = tk.Canvas(frame, width=20, height=20)
            sample.pack(side=tk.LEFT, padx=5)
            sample.create_rectangle(2, 2, 18, 18, fill=LAYER_COLORS[value], outline="black")
            
            # Label
            tk.Label(frame, text=label).pack(side=tk.LEFT)

    def draw_grid(self):
        """Draws the grid with all layers"""
        # Start with empty grid
        for i in range(len(self.base_grid)):
            for j in range(len(self.base_grid[0])):
                x1, y1 = j * self.cell_size, i * self.cell_size
                x2, y2 = (j + 1) * self.cell_size, (i + 1) * self.cell_size
                
                # Get cell value from each layer
                cell_value = 0
                if self.base_grid[i][j] == 1:
                    cell_value = 1
                if self.grid_data["entrances.geojson"][i][j] == 1:
                    cell_value = 2
                if self.grid_data["hallways.geojson"][i][j] == 1:
                    cell_value = 3
                
                color = LAYER_COLORS[cell_value]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")

    def set_start(self, event):
        """Handles setting the start position."""
        x, y = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= y < len(self.base_grid) and 0 <= x < len(self.base_grid[0]):
            # Allow start point on entrances (2) or hallways (3)
            cell_value = 0
            if self.base_grid[y][x] == 1:
                cell_value = 1
            if self.grid_data["entrances.geojson"][y][x] == 1:
                cell_value = 2
            if self.grid_data["hallways.geojson"][y][x] == 1:
                cell_value = 3
                
            if cell_value in [0, 2, 3]:  # Allow on empty space, entrances, or hallways
                self.start = (y, x)
                self.update_grid()
                self.run_pathfinding()

    def set_end(self, event):
        """Handles setting the end position."""
        x, y = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= y < len(self.base_grid) and 0 <= x < len(self.base_grid[0]):
            # Allow end point on entrances (2) or hallways (3)
            cell_value = 0
            if self.base_grid[y][x] == 1:
                cell_value = 1
            if self.grid_data["entrances.geojson"][y][x] == 1:
                cell_value = 2
            if self.grid_data["hallways.geojson"][y][x] == 1:
                cell_value = 3
                
            if cell_value in [0, 2, 3]:  # Allow on empty space, entrances, or hallways
                self.end = (y, x)
                self.update_grid()
                self.run_pathfinding()

    def update_grid(self):
        """Redraws grid with start (yellow) and end (magenta) markers."""
        self.draw_grid()
        if self.start:
            sx, sy = self.start[1] * self.cell_size, self.start[0] * self.cell_size
            self.canvas.create_rectangle(sx, sy, sx + self.cell_size, sy + self.cell_size, fill="yellow", outline="black")
        if self.end:
            ex, ey = self.end[1] * self.cell_size, self.end[0] * self.cell_size
            self.canvas.create_rectangle(ex, ey, ex + self.cell_size, ey + self.cell_size, fill="magenta", outline="black")

    def get_pathfinding_grid(self):
        """Creates a grid suitable for pathfinding where 1 is non-traversable and 0 is traversable"""
        grid_height = len(self.base_grid)
        grid_width = len(self.base_grid[0])
        pathfinding_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
        
        for i in range(grid_height):
            for j in range(grid_width):
                # Start with checking if it's a building
                if self.base_grid[i][j] == 1:
                    pathfinding_grid[i][j] = 1
                
                # If it's an entrance or hallway, mark as traversable (0)
                if (self.grid_data["entrances.geojson"][i][j] == 1 or 
                    self.grid_data["hallways.geojson"][i][j] == 1):
                    pathfinding_grid[i][j] = 0
        
        return pathfinding_grid

    def run_pathfinding(self):
        """Runs A* algorithm if both start and end are selected and draws the path."""
        if self.start and self.end:
            # Get grid suitable for pathfinding
            pathfinding_grid = self.get_pathfinding_grid()
            
            # Find path
            path = a_star(pathfinding_grid, self.start, self.end, custom_padding=0)  # No padding needed
            
            # Draw path
            if path:
                # Clear any existing path
                self.draw_grid()
                
                # Draw new path
                for y, x in path:
                    if (y, x) != self.start and (y, x) != self.end:
                        px, py = x * self.cell_size, y * self.cell_size
                        self.canvas.create_rectangle(px, py, px + self.cell_size, py + self.cell_size, fill="cyan", outline="black")

def main():
    grid_file = "c:/Users/not3t/CampusNav/campus-navigator/packages/data-processing/grid_storage.json"
    grid_data = read_json_file(grid_file)

    root = tk.Tk()
    root.title("Campus Navigator")
    app = GridApp(root, grid_data)
    root.mainloop()

if __name__ == '__main__':
    main()