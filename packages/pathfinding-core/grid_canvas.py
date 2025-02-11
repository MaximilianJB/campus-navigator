import tkinter as tk
import random

def draw_grid(canvas, grid, cell_size):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Fill in squares based on grid values: 0 -> white, 1 -> black
    for i in range(rows):
        for j in range(cols):
            x1, y1 = j * cell_size, i * cell_size
            x2, y2 = (j + 1) * cell_size, (i + 1) * cell_size
            color = "white" if grid[i][j] == 0 else "black"
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    # Draw plain black grid lines over the squares
    width = cols * cell_size
    height = rows * cell_size
    for i in range(rows + 1):
        canvas.create_line(0, i * cell_size, width, i * cell_size, fill="black")
    for j in range(cols + 1):
        canvas.create_line(j * cell_size, 0, j * cell_size, height, fill="black")

def main():
    # Define the 2D grid array (0: white, 1: black) for a 40x20 grid
    grid = [[1 if random.random() < 0.3 else 0 for _ in range(40)] for _ in range(20)]

    cell_size = 20  # Size of each grid cell in pixels
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    canvas_width = cols * cell_size
    canvas_height = rows * cell_size

    # Create Tkinter window and canvas
    root = tk.Tk()
    root.title("Pathfinding Grid Canvas")
    canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
    canvas.pack()

    draw_grid(canvas, grid, cell_size)

    root.mainloop()

if __name__ == '__main__':
    main()