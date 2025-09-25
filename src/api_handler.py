import json
import os

import boto3

S3_BUCKET = os.getenv("DATA_BUCKET")
CURR_KEY = os.getenv("DATA_KEY", "ecfr/agency_sizes.json")

s3 = boto3.client("s3")


def _get_cached():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=CURR_KEY)
        raw = obj["Body"].read()
        return json.loads(raw)
    except Exception:
        return None


def handler(event, _context):
    doc = _get_cached()

    if doc is None:
        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Data not available. Ingestion in progress."}),
        }

    if "agencies" in doc and doc["agencies"]:
        agencies_mb_only = {agency: data["mb"] for agency, data in doc["agencies"].items()}

        # Get sort parameter from query string (default: size descending)
        sort_by = "size"
        if event and "queryStringParameters" in event and event["queryStringParameters"]:
            sort_by = event["queryStringParameters"].get("sort", "size")

        # Apply sorting based on parameter
        if sort_by == "name":
            agencies_sorted = dict(sorted(agencies_mb_only.items(), key=lambda x: x[0]))
        elif sort_by == "size_asc":
            agencies_sorted = dict(sorted(agencies_mb_only.items(), key=lambda x: x[1]))
        else:  # default: "size" (descending)
            agencies_sorted = dict(
                sorted(agencies_mb_only.items(), key=lambda x: x[1], reverse=True)
            )

        doc = {
            "updated_at": doc["updated_at"],
            "source": doc["source"],
            "units": doc["units"],
            "agencies": agencies_sorted,
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=300",
        },
        "body": json.dumps(doc),
    }
