import json
import os
import boto3
import psycopg2
import urllib.request
from urllib.parse import urlparse
from app.auth import require_auth

# Import rating logic
from metric_calculator import MetricCalculator
from url_handler import URLHandler
from url_category import URLCategory
from url_data import URLData
from data_retrieval import DataRetriever

S3_BUCKET = os.environ.get("S3_BUCKET")
SECRET_NAME = os.environ.get("SECRET_NAME", "DB_CREDS")

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")


def get_db_connection():
    """Retrieve DB credentials from Secrets Manager and connect to Postgres."""
    secret_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    secret = json.loads(secret_response["SecretString"])
    return psycopg2.connect(
        host=secret["host"],
        port=secret["port"],
        dbname=secret["dbname"],
        user=secret["username"],
        password=secret["password"],
    )


def parse_huggingface_url(url: str):
    """Extract model identifier from Hugging Face URL."""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def list_huggingface_files(identifier: str):
    """Return list of file paths for a Hugging Face model."""
    api_url = f"https://huggingface.co/api/models/{identifier}"
    with urllib.request.urlopen(api_url) as response:
        data = json.load(response)
        siblings = data.get("siblings", [])
        return [file["rfilename"] for file in siblings]


def download_and_upload_to_s3(identifier: str, artifact_type: str, artifact_id: int):
    """Stream all model files from HF → directly to S3."""
    files = list_huggingface_files(identifier)
    for filename in files:
        hf_file_url = f"https://huggingface.co/{identifier}/resolve/main/{filename}"
        s3_key = f"{artifact_type}/{artifact_id}/{filename}"
        try:
            with urllib.request.urlopen(hf_file_url) as response:
                s3_client.upload_fileobj(response, S3_BUCKET, s3_key)
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")




def lambda_handler(event, context):

    # 403 AUTHENTICATION FAILED
    valid, error = require_auth(event)
    if not valid:
        return error
    
    try:
        body = json.loads(event.get("body", "{}"))
        url = body.get("url")
        artifact_type = event.get("pathParameters", {}).get("artifact_type")

        if not url or not artifact_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing URL or artifact_type"})
            }

        identifier = parse_huggingface_url(url)
        if not identifier:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid Hugging Face URL"})
            }
        
        # DUPLICATE CHECK (409)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM artifacts WHERE url = %s AND type = %s;",
            (url, artifact_type)
        )
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return {
                "statusCode": 409,
                "body": json.dumps({"error": "Artifact already exists", "id": existing[0]})
            }
        
        # RATING PIPELINE (424 / 202 / 201)
        url_handler = URLHandler()
        data_retriever = DataRetriever(
            github_token=os.environ.get("GITHUB_TOKEN"),
            hf_token=os.environ.get("HF_TOKEN")
        )
        metric_calc = MetricCalculator()

        # Build synthetic model data (minimal needed for calculator)
        model_obj = URLData(url=url, category=URLCategory.HUGGINGFACE, is_valid=True)

        repo_data = data_retriever.retrieve_data(model_obj)
        model_dict = {
            **repo_data.__dict__,
            "name": identifier
        }

        rating = metric_calc.calculate_all_metrics(model_dict, category="MODEL")
        net_score = rating["net_score"]

        # Disqualified
        if net_score < 0.5:
            return {
                "statusCode": 424,
                "body": json.dumps({
                    "error": "Artifact is not registered due to disqualified rating.",
                    "net_score": net_score
                })
            }



        # --- Insert DB record ---
        cur.execute(
            "INSERT INTO artifacts (type, url, name) VALUES (%s, %s, %s) RETURNING id;",
            (artifact_type, url, identifier, net_score),   #### added net_score
        )
        artifact_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # --- Download all files to S3 ---
        download_and_upload_to_s3(identifier, artifact_type, artifact_id)

        # SUCCESS RESPONSE (201)
        return {
            "statusCode": 201,
            "body": json.dumps({
                "metadata": {
                    "name": identifier,
                    "id": artifact_id,
                    "type": artifact_type
                },
                "data": {
                    "url": url,
                    "download_url": f"s3://{S3_BUCKET}/{artifact_type}/{artifact_id}/"
                }
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
