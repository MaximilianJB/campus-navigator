# Pathfinding Core

This repository contains an implementation of the **A\*** pathfinding algorithm, optimized using Euclidean distance minimization as a heuristic. The algorithm calculates the shortest path between two points on a grid representation of a custom GeoJSON campus map.

## Files Overview

### `a_star.py`
- Implements the **A\*** pathfinding algorithm.
- Accepts a **2D grid** representation of a map, a **start coordinate**, and an **end coordinate**.
- Returns a **list of grid coordinates** representing the shortest path.

### Testing & Visualization

#### `grid_canvas.py` (GUI-Based Testing)
- Runs a **graphical interface** for testing the algorithm.
- Opens a **campus grid map** in a GUI window.
- **Left-click** to set the **start point**.
- **Right-click** to set the **end point**.
- The computed **shortest path** will appear as a **blue line** after a few seconds.

#### `path_mapping.py` (API-Based Testing)
- Tests the **pathfinding algorithm** on a hosted API.
- Takes in **start and end latitude/longitude coordinates**.
- Returns a path as a list of **lat/lon coordinates**.
- Uses **Folium** to visualize the path on an interactive map.
- Generates an **HTML file** that can be opened in a browser.

## Usage
- Run `grid_canvas.py` for local GUI-based testing.
- Run `path_mapping.py` for API-based testing and map visualization.