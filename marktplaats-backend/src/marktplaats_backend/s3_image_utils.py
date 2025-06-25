import os
import base64
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Force AWS region to eu-west-1
os.environ['AWS_REGION'] = 'eu-west-1'


def upload_image_to_s3(image_base64, bucket_name=None):
    """
    Upload a base64 encoded image to S3 and return a public URL.
    
    Args:
        image_base64 (str): Base64 encoded image data
        bucket_name (str): S3 bucket name (defaults to env var)
    
    Returns:
        str: Public URL of the uploaded image
        
    Raises:
        ValueError: If image data is invalid
        ClientError: If S3 upload fails
    """
    if not bucket_name:
        bucket_name = os.environ.get('S3_BUCKET', 'marktplaatser-images')
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"listings/{timestamp}_{unique_id}.jpg"
        
        # Create S3 client
        session = boto3.Session(region_name="eu-west-1")
        s3_client = session.client('s3')
        
        # Upload image (bucket configured for public access)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=image_data,
            ContentType='image/jpeg'
        )
        
        # Generate pre-signed URL (valid for 24 hours)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': filename},
            ExpiresIn=86400  # 24 hours
        )
        
        return presigned_url
        
    except Exception as e:
        raise ValueError(f"Failed to upload image to S3: {str(e)}")


def delete_image_from_s3(image_url, bucket_name=None):
    """
    Delete an image from S3 using its public URL.
    
    Args:
        image_url (str): Public URL of the image
        bucket_name (str): S3 bucket name (defaults to env var)
        
    Returns:
        bool: True if deletion was successful
    """
    if not bucket_name:
        bucket_name = os.environ.get('S3_BUCKET', 'marktplaatser-images')
    
    try:
        # Extract filename from URL (handle both regular and pre-signed URLs)
        if f"{bucket_name}.s3.eu-west-1.amazonaws.com/" in image_url:
            filename = image_url.split(f"{bucket_name}.s3.eu-west-1.amazonaws.com/")[1].split("?")[0]
        else:
            # Extract from different URL format if needed
            filename = image_url.split("/")[-1].split("?")[0]
        
        # Create S3 client
        session = boto3.Session(region_name="eu-west-1")
        s3_client = session.client('s3')
        
        # Delete object
        s3_client.delete_object(Bucket=bucket_name, Key=filename)
        
        return True
        
    except Exception as e:
        print(f"Failed to delete image from S3: {str(e)}")
        return False


def verify_image_accessible(image_url):
    """
    Verify that an uploaded image is accessible via its URL.
    
    Args:
        image_url (str): URL of the image (can be pre-signed)
        
    Returns:
        bool: True if image is accessible
    """
    import requests
    
    try:
        # For pre-signed URLs, do a GET request to check accessibility
        response = requests.get(image_url, timeout=10, stream=True)
        
        # Check if we get a successful response and it's an image
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if content_type.startswith('image/'):
                return True
                
        return False
    except Exception as e:
        print(f"Image accessibility check failed: {e}")
        return False