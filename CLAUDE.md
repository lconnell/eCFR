# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a serverless Python application that provides an API for federal agency regulation size data from the eCFR (Electronic Code of Federal Regulations). The architecture uses:

- **Ingestor Lambda** (`src/compute_sizes.py`) - scheduled daily via EventBridge to fetch eCFR data and compute agency regulation sizes
- **API Lambda** (`src/api_handler.py`) - serves cached data via API Gateway HTTP API at `/agencies` endpoint
- **eCFR Client** (`src/ecfr_client.py`) - core logic for fetching and processing eCFR JSON data
- **S3** - stores current snapshot (`ecfr/agency_sizes.json`) and dated archives with 15-day lifecycle
- **Terraform** - infrastructure as code in the `infra/` directory

## Development Commands

All development tasks use **go-task** (Taskfile.yml):

```bash
# Setup Python environment with uv
task setup

# Format and lint Python code (uses black + ruff)
task fmt

# Build Lambda layer with dependencies
task layer:build

# Terraform operations
task tf:init
task tf:plan
task tf:apply
task tf:destroy

# Complete deployment (format, build layer, terraform apply)
task deploy

# Get API URL and test
task url
task curl

# Run the eCFR client directly (for testing)
task run

# Troubleshooting commands
task ingest    # Manually trigger ingestor Lambda
task logs      # View recent Lambda logs
task debug     # Show Lambda environment and config
```

## Code Style and Linting

- **Python 3.12** target with line length 100 (configured in `pyproject.toml`)
- **Ruff** linter with rules E, F, W, I enabled
- Always run `task fmt` before committing changes
- Code uses `uv` for Python package management
- Dependencies listed in `requirements.txt` (runtime) and installed via `uv`

## Key Environment Variables

Lambda functions use these configurable environment variables (set via Terraform):
- `ECFR_BASE_URL` - eCFR API base URL (default: https://www.ecfr.gov)
- `ECFR_STRUCTURE_JSON_PATH_TMPL` - URL template for structure JSON endpoints
- `ECFR_AGENCIES_PATH` - Path for agencies API endpoint
- `ECFR_DATE` - Override date for data fetching (defaults to "current")
- `ECFR_POLITE_DELAY_SECONDS` - Rate limiting delay between requests (default: 0.15)
- `HTTP_USER_AGENT` - User agent for HTTP requests
- `DATA_BUCKET`, `DATA_KEY` - S3 storage configuration
- `DATA_TTL_HOURS` - Cache TTL (default: 26 hours)

## Architecture Notes

- The system separates data ingestion (scheduled) from API serving (on-demand) for performance
- Agency attribution uses heuristic field matching in `ECFRClient._guess_agency()`
- Text size calculation sums UTF-8 byte counts from text-bearing JSON fields
- API supports `?refresh=true` for inline recomputation when cache is stale
- S3 lifecycle automatically deletes archive files older than 15 days
- Rate limiting built into eCFR client with configurable delay between requests

## Testing the API

After deployment:
```bash
# Get the API endpoint URL
task url

# Test the agencies endpoint
task curl
```

The API returns JSON with agency regulation sizes in MB, including metadata about update time and data source.