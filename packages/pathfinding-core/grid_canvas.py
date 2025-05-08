import tkinter as tk
import json
from a_star import a_star, apply_padding

# Constants
SQUARE_SIZE = 2
PATH_SMOOTHING = 0.5  # Adjustable smoothing factor (0 to 1)

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
                self.find_path()

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
                self.find_path()

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
        
        # First, mark buildings
        for i in range(grid_height):
            for j in range(grid_width):
                if self.base_grid[i][j] == 1:
                    pathfinding_grid[i][j] = 1
        
        # Get hallways and entrances
        hallways_and_entrances = set()
        for i in range(grid_height):
            for j in range(grid_width):
                if (self.grid_data["entrances.geojson"][i][j] == 1 or 
                    self.grid_data["hallways.geojson"][i][j] == 1):
                    hallways_and_entrances.add((i, j))
                    # Add adjacent cells to ensure good connectivity
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            ni, nj = i + di, j + dj
                            if (0 <= ni < grid_height and 
                                0 <= nj < grid_width):
                                hallways_and_entrances.add((ni, nj))
        
        # Apply graduated padding to buildings
        from a_star import apply_padding
        pathfinding_grid = apply_padding(pathfinding_grid, 2)  # Use smaller padding
        
        # Make hallways and entrances fully traversable
        for i, j in hallways_and_entrances:
            pathfinding_grid[i][j] = 0
        
        return pathfinding_grid

    def find_path(self):
        """Find and draw path between start and end points"""
        if self.start and self.end:
            # Get grid suitable for pathfinding
            pathfinding_grid = self.get_pathfinding_grid()
            
            # Find path
            path = a_star(pathfinding_grid, self.start, self.end)
            
            if path:
                # Clear any existing path
                self.draw_grid()
                
                # Draw the smooth path
                self.draw_path(path)
                
                # Mark start and end points
                if self.start:
                    sx, sy = self.start[1] * self.cell_size, self.start[0] * self.cell_size
                    self.canvas.create_rectangle(sx, sy, sx + self.cell_size, sy + self.cell_size, 
                                              fill="yellow", outline="black")
                if self.end:
                    ex, ey = self.end[1] * self.cell_size, self.end[0] * self.cell_size
                    self.canvas.create_rectangle(ex, ey, ex + self.cell_size, ey + self.cell_size, 
                                              fill="magenta", outline="black")

    def draw_path(self, path):
        """Draw the path with smooth curves"""
        if not path:
            return
        
        # Draw the smooth path
        if len(path) > 1:
            # Convert points to flat list for create_line
            flat_coords = []
            for x, y in path:
                flat_coords.extend([x, y])
            
            # Draw smooth curve
            self.canvas.create_line(
                flat_coords,
                fill=LAYER_COLORS[9],
                width=self.cell_size,  # Line width matches cell size
                capstyle=tk.ROUND,     # Round end caps
                joinstyle=tk.ROUND,    # Round corners
                smooth=True            # Enable smoothing
            )
            
            # Draw start and end markers
            start_x, start_y = path[0]
            end_x, end_y = path[-1]
            
            # Start marker (yellow)
            self.canvas.create_oval(
                start_x - self.cell_size, start_y - self.cell_size,
                start_x + self.cell_size, start_y + self.cell_size,
                fill="yellow", outline="black"
            )
            
            # End marker (magenta)
            self.canvas.create_oval(
                end_x - self.cell_size, end_y - self.cell_size,
                end_x + self.cell_size, end_y + self.cell_size,
                fill="magenta", outline="black"
            )

def main():
    grid_file = "/Users/maximilianbrown/Desktop/GU/Senior/CampusNav/campus-navigator/packages/data-processing/grid_config_gu.json"
    grid_data = read_json_file(grid_file)

    root = tk.Tk()
    root.title("Campus Navigator")
    app = GridApp(root, grid_data["grid"])
    root.mainloop()

if __name__ == '__main__':
    main()  