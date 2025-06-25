import boto3

def extract_labels_and_text(image_bytes):
    client = boto3.client("rekognition")

    # Detect labels from image bytes
    label_response = client.detect_labels(
        Image={"Bytes": image_bytes},
        MaxLabels=10,
        MinConfidence=75
    )
    labels = [label["Name"] for label in label_response.get("Labels", [])]

    # Detect text from image bytes
    text_response = client.detect_text(
        Image={"Bytes": image_bytes}
    )
    text_detections = text_response.get("TextDetections", [])
    text_lines = [
        text["DetectedText"]
        for text in text_detections
        if text["Type"] == "LINE"
    ]

    return labels, text_lines
