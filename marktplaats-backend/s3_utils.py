import boto3

s3 = boto3.client("s3")


def upload_image_to_s3(image_bytes, bucket_name, key):
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType="image/jpeg",
        ACL="bucket-owner-full-control",
    )

    # Generate presigned URL (valid for 1 hour)
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=3600,
    )

    return url
