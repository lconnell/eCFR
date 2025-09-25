import json
import os
from datetime import datetime, timezone

import boto3

from ecfr_client import ECFRClient

S3_BUCKET = os.getenv("DATA_BUCKET")
CURR_KEY = os.getenv("DATA_KEY", "ecfr/agency_sizes.json")
ARCHIVE_PREFIX = os.getenv("ARCHIVE_PREFIX", "ecfr/archives/")
TTL_HOURS = int(os.getenv("DATA_TTL_HOURS", "26"))

s3 = boto3.client("s3")


def put_json(bucket: str, key: str, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
        CacheControl=f"max-age={TTL_HOURS * 3600}",
    )


def handler(event, context):
    client = ECFRClient()
    sizes = client.compute_agency_sizes_mb()
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "updated_at": now,
        "source": "eCFR",
        "units": "MB (approx, text length based)",
        "agencies": sizes,
    }
    # Write current snapshot
    put_json(S3_BUCKET, CURR_KEY, payload)

    # Write dated archive for lifecycle cleanup
    date_part = now[:10]
    archive_key = f"{ARCHIVE_PREFIX}agency_sizes_{date_part}.json"
    put_json(S3_BUCKET, archive_key, payload)

    return {"status": "ok", "agencies": len(sizes), "snapshot": CURR_KEY, "archive": archive_key}
