"""
Google Cloud Storage utilities
"""
import json
from google.cloud import storage

# Default Cloud Storage bucket name
DEFAULT_BUCKET_NAME = 'gu-campus-maps'
DEFAULT_CONFIG_FILE = 'grid_config.json'

def download_grid_config(bucket_name=DEFAULT_BUCKET_NAME, file_name=DEFAULT_CONFIG_FILE):
    """Download and parse grid_config.json from Cloud Storage.
    
    Args:
        bucket_name (str): The GCS bucket name
        file_name (str): The file name to download
        
    Returns:
        dict: Parsed JSON configuration
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    return json.loads(blob.download_as_text())
