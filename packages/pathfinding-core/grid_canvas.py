import tkinter as tk
import json
from a_star import a_star

# Constants
SQUARE_SIZE = 2

def read_json_file(file_path):
    # Function that reads the grid json file and returns a 2D grid array representation
    with open(file_path, "r") as file:
        json_data = json.load(file)
        
        # iterate over json rows
        grid = []
        for row in json_data['campus1.geojson']:
            grid_row = []
            for cell in row:
                grid_row.append(cell)
            grid.append(grid_row)
            
        return grid
class GridApp:
    def __init__(self, root, grid):
        self.root = root
        self.grid = grid
        self.cell_size = SQUARE_SIZE
        self.start = None
        self.end = None
        self.canvas = tk.Canvas(root, width=len(grid[0]) * self.cell_size, height=len(grid) * self.cell_size)
        self.canvas.pack()
        self.draw_grid()
        self.canvas.bind("<Button-1>", self.set_start)  # Left-click to set start
        self.canvas.bind("<Button-3>", self.set_end)  # Right-click to set end

    def draw_grid(self):
        """Draws the grid based on 0 (white) and 1 (black) values."""
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                x1, y1 = j * self.cell_size, i * self.cell_size
                x2, y2 = (j + 1) * self.cell_size, (i + 1) * self.cell_size
                color = "white" if self.grid[i][j] == 0 else "black"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")

    def set_start(self, event):
        """Handles setting the start position."""
        x, y = event.x // self.cell_size, event.y // self.cell_size
        print(f"X: {x}, Y: {y}")
        if self.grid[y][x] == 0:  # Ensure it's a traversable square
            self.start = (y, x)
            self.update_grid()
            self.run_pathfinding()

    def set_end(self, event):
        """Handles setting the end position."""
        x, y = event.x // self.cell_size, event.y // self.cell_size
        print(f"X: {x}, Y: {y}")
        if self.grid[y][x] == 0:  # Ensure it's a traversable square
            self.end = (y, x)
            self.update_grid()
            self.run_pathfinding()

    def update_grid(self):
        """Redraws grid with start (green) and end (red) markers."""
        self.draw_grid()
        if self.start:
            sx, sy = self.start[1] * self.cell_size, self.start[0] * self.cell_size
            self.canvas.create_rectangle(sx, sy, sx + self.cell_size, sy + self.cell_size, fill="green", outline="black")
        if self.end:
            ex, ey = self.end[1] * self.cell_size, self.end[0] * self.cell_size
            self.canvas.create_rectangle(ex, ey, ex + self.cell_size, ey + self.cell_size, fill="red", outline="black")

    def run_pathfinding(self):
        """Runs A* algorithm if both start and end are selected and draws the path."""
        if self.start and self.end:
            path = a_star(self.grid, self.start, self.end)
            if path:
                for y, x in path:
                    if (y, x) != self.start and (y, x) != self.end:
                        px, py = x * self.cell_size, y * self.cell_size
                        self.canvas.create_rectangle(px, py, px + self.cell_size, py + self.cell_size, fill="blue", outline="black")


def main():
    grid = read_json_file("/Users/maximilianbrown/Desktop/GU/Senior/CampusNav/campus-navigator/packages/data-processing/grid_storage.json")

    root = tk.Tk()
    root.title("Pathfinding Grid Selector")
    app = GridApp(root, grid)
    root.mainloop()

if __name__ == '__main__':
    main()