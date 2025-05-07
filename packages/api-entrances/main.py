"""
Main entry point for the Building Entrances Processing API
"""
import os
from src.app import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8081
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
