import os
import json
import boto3
import urllib.request
from urllib.parse import urlparse

sqs = boto3.client("sqs")
s3 = boto3.client("s3")
secrets = boto3.client("secretsmanager")

QUEUE_URL = os.environ["QUEUE_URL"]
S3_BUCKET = os.environ["S3_BUCKET"]
SECRET_NAME = os.environ["SECRET_NAME"]

def parse_hf_identifier(url: str):
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None

def list_hf_files(identifier: str):
    api_url = f"https://huggingface.co/api/models/{identifier}"
    with urllib.request.urlopen(api_url) as response:
        data = json.load(response)
        siblings = data.get("siblings", [])
        return [file["rfilename"] for file in siblings]

def stream_file_to_s3(url, bucket, key):
    with urllib.request.urlopen(url) as response:
        s3.upload_fileobj(response, bucket, key)

print("Worker started. Waiting for messages...")

while True:
    resp = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )

    if "Messages" not in resp:
        continue

    msg = resp["Messages"][0]
    receipt = msg["ReceiptHandle"]
    body = json.loads(msg["Body"])

    artifact_id = body["artifact_id"]
    artifact_type = body["artifact_type"]
    url = body["url"]

    try:
        identifier = parse_hf_identifier(url)
        files = list_hf_files(identifier)

        for filename in files:
            hf_url = f"https://huggingface.co/{identifier}/resolve/main/{filename}"
            s3_key = f"{artifact_type}/{artifact_id}/{filename}"
            print(f"Uploading {filename}...")
            stream_file_to_s3(hf_url, S3_BUCKET, s3_key)

        print("Ingest complete!")

    except Exception as e:
        print("Error:", e)

    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt)
