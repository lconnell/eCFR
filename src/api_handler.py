import json
import os
from datetime import datetime, timedelta, timezone

import boto3

from ecfr_client import ECFRClient

S3_BUCKET = os.getenv("DATA_BUCKET")
CURR_KEY = os.getenv("DATA_KEY", "ecfr/agency_sizes.json")
MAX_AGE_HOURS = int(os.getenv("DATA_TTL_HOURS", "26"))

s3 = boto3.client("s3")


def _get_cached():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=CURR_KEY)
        raw = obj["Body"].read()
        return json.loads(raw)
    except Exception:
        return None


def _is_stale(doc):
    try:
        ts = datetime.fromisoformat(doc.get("updated_at").replace("Z", "+00:00"))
    except Exception:
        return True
    return datetime.now(timezone.utc) - ts > timedelta(hours=MAX_AGE_HOURS)


def handler(event, context):
    qs = event.get("rawQueryString") or ""
    refresh = "refresh=true" in qs

    doc = _get_cached()

    if (doc is None) or refresh or _is_stale(doc):
        client = ECFRClient()
        sizes = client.compute_agency_sizes_mb()
        doc = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": "eCFR",
            "units": "MB (approx, text length based)",
            "agencies": sizes,
        }
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=CURR_KEY,
                Body=json.dumps(doc).encode("utf-8"),
                ContentType="application/json",
                CacheControl=f"max-age={MAX_AGE_HOURS * 3600}",
            )
        except Exception:
            pass

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=300",
        },
        "body": json.dumps(doc),
    }
