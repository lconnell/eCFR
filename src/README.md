# eCFR Agency Size Tracker (Bottle Version)

A simplified version of the eCFR API that runs locally using the Bottle web framework.

## Features

- Fetches agency size data from the eCFR (Electronic Code of Federal Regulations) API
- Displays agency sizes in a web interface
- Caches data locally in JSON format
- Provides both web UI and JSON API endpoints
- Includes data refresh functionality

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python ecfr_bottle_app.py
```

3. Open http://localhost:8080 in your browser

## Usage

- **Main page** (`/`): View agency data in a sortable table
- **API endpoint** (`/api/agencies`): Get JSON data (supports `?sort=name`, `?sort=size`, `?sort=size_asc`)
- **Refresh data** (`/refresh`): Fetch fresh data from eCFR API

## Data Storage

Data is cached locally in `agency_sizes.json` in the same directory as the script.

## API Reference

The application provides a simple JSON API:

```
GET /api/agencies?sort=size
```

Query parameters:
- `sort`: Sort order - `name`, `size`, or `size_asc` (default: `size`)

Response format:
```json
{
  "updated_at": "2023-12-01T10:30:00Z",
  "source": "eCFR",
  "units": "MB (approx, text length based)",
  "agencies": {
    "Department of Agriculture": {
      "bytes": 123456789,
      "mb": 117.737,
      "titles": 5
    }
  }
}
```
