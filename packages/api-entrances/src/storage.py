"""
Google Cloud Storage utilities
"""
import json
from google.cloud import storage

# Define GCS bucket for storing processed JSON files
DEFAULT_BUCKET_NAME = 'gu-campus-maps'

def upload_to_gcs(data, bucket_name=DEFAULT_BUCKET_NAME, blob_path=None):
    """Upload JSON data to Google Cloud Storage.
    
    Args:
        data: The data to upload (will be converted to JSON)
        bucket_name (str): The name of the GCS bucket
        blob_path (str): The path within the bucket where the file should be stored
        
    Returns:
        str: Public URL of the uploaded file
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    # Convert data to JSON string and upload
    json_data = json.dumps(data, indent=2)
    blob.upload_from_string(json_data, content_type='application/json')
    
    return blob.public_url
