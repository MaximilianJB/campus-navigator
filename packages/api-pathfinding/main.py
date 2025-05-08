"""
Main entry point for the Campus Pathfinding API
"""
import os
from src.app import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
