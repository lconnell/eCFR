# eCFR Agency Regulation Size API (Serverless)

A simple serverless API that reports, for each federal agency, an approximate **size (MB)** of its
regulations found in the eCFR. It updates within **24 hours** using a daily precompute job.

## Architecture (why a scheduler *and* an API)

- **Ingestor Lambda** (scheduled daily by **EventBridge**) pulls the latest eCFR JSON endpoints,
  computes per‑agency text size, and writes two S3 objects:
  - Current snapshot: `ecfr/agency_sizes.json`
  - Dated archive: `ecfr/archives/agency_sizes_YYYY-MM-DD.json` (S3 Lifecycle deletes archives after 15 days)
- **API Lambda** behind **API Gateway HTTP API** serves `/agencies` quickly from S3. It can optionally
  recompute inline when the cache is missing or stale (best‑effort).

This meets the “reflect changes within 24 hours” requirement without modifying source code and avoids
slow/costly live crawls on every request.

## JSON endpoints (configurable)

This project prefers **JSON** over XML. You can configure the URL template via Terraform variables
(see **Updating endpoints** below) without any code changes:

- `ecfr_base_url` (default: `https://www.ecfr.gov`)
- `ecfr_title_json_path_tmpl` (default: `/api/versioner/v1/full/{date}/title-{title}.json`)

The client will iterate titles `1..50` by default (configurable via env `ECFR_MAX_TITLES`). For each
title, it attempts to attribute chapter sections to an agency using common JSON fields, and falls back
to reasonable labels if needed. Size is computed as text byte counts (approximate MB).

## Prereqs

- **Terraform 1.13.3+**
- AWS credentials with permissions for Lambda, API Gateway, EventBridge, S3, IAM
- **go-task** (https://github.com/go-task/task)
- **uv** (https://github.com/astral-sh/uv) for Python env/package mgmt
- Python 3.12 on your dev machine (for formatting/lint only)

## Common tasks

```bash
# 1) Setup local tooling
task setup

# 2) Lint/format
task fmt

# 3) Build Lambda layer (requests)  -> layer.zip
task layer:build

# 4) Plan/apply infra (uses infra/env.dev.tfvars)
task tf:plan
task tf:apply

# Or do it all:
task deploy

# 5) Get API URL and test
task url
task curl
```

## Updating endpoints / date

All endpoint settings are **variables** or **env vars**:

- **Terraform variables** (no code change, no rebuild):
  - `ecfr_base_url`
  - `ecfr_title_json_path_tmpl`
  - `http_user_agent`

Edit `infra/env.dev.tfvars` then:

```bash
task tf:apply
```

- **Lambda env vars** (set by Terraform):
  - `ECFR_MAX_TITLES` (default 50)
  - `ECFR_DATE` (optional override; defaults to `today` in UTC)

## API

- **GET** `/agencies`
  - Returns latest snapshot JSON.
  - Optional `?refresh=true` will attempt an inline recompute (best‑effort).

Example:
```json
{
  "updated_at": "2025-09-24T14:11:22.123456+00:00",
  "source": "eCFR",
  "units": "MB (approx, text length based)",
  "agencies": {
    "Department of Transportation": { "bytes": 12345678, "mb": 11.773, "titles": [14, 23, 49] },
    "Environmental Protection Agency": { "bytes": 23456789, "mb": 22.383, "titles": [40] }
  }
}
```

## Notes / Caveats

- **Heuristic attribution**: If an explicit agency field isn’t present, chapters are grouped by their
  header/label. For better fidelity you can add a mapping table later.
- **Lifecycle**: S3 automatically deletes `ecfr/archives/*` objects older than **15 days**.
- **Dependencies**: Runtime third‑party deps are shipped in a **custom Lambda layer** (`requests`).
- **Cost/rate‑limits**: Ingestor rate‑limits itself; parallelism can be added if needed.

## License
MIT
