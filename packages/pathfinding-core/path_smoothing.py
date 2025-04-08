import numpy as np
from scipy.interpolate import splprep, splev

def smooth_path(path_points, smoothing_factor=0.5, num_points=100):
    """
    Smooth a path using B-splines.
    
    Args:
        path_points: List of (x, y) tuples representing the path
        smoothing_factor: Controls how closely the spline follows the original points (0 to 1)
        num_points: Number of points to generate along the smoothed path
    
    Returns:
        Tuple of (x_smooth, y_smooth) arrays representing the smoothed path
    """
    if len(path_points) < 4:  # Need at least 4 points for a cubic spline
        return list(zip(*path_points))  # Return original points if too few
        
    # Separate x and y coordinates
    x_points = [p[0] for p in path_points]
    y_points = [p[1] for p in path_points]
    
    # Convert to numpy arrays
    points = np.array([x_points, y_points])
    
    # Calculate the smoothing parameter (s)
    # Higher values = more smoothing
    s = len(path_points) * smoothing_factor
    
    try:
        # Fit the spline
        tck, u = splprep(points, s=s, k=3)  # k=3 for cubic spline
        
        # Generate points along the spline
        u_new = np.linspace(0, 1, num_points)
        x_smooth, y_smooth = splev(u_new, tck)
        
        return x_smooth, y_smooth
    except Exception as e:
        print(f"Warning: Could not smooth path: {e}")
        return list(zip(*path_points))  # Return original points if smoothing fails

def get_smooth_path_points(path, cell_size, smoothing_factor=0.5):
    """
    Convert grid path to smooth path points.
    
    Args:
        path: List of (row, col) grid coordinates
        cell_size: Size of each grid cell
        smoothing_factor: Controls path smoothness (0 to 1)
    
    Returns:
        List of (x, y) points representing the smoothed path
    """
    # Convert grid coordinates to pixel coordinates
    path_points = [(col * cell_size + cell_size/2, row * cell_size + cell_size/2) 
                  for row, col in path]
    
    # Get smoothed path
    x_smooth, y_smooth = smooth_path(path_points, smoothing_factor)
    
    return list(zip(x_smooth, y_smooth))
