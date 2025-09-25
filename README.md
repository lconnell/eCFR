# eCFR Agency Regulation Size Analyzer

A Python package that analyzes the [eCFR](https://www.ecfr.gov/) to calculate the size of regulations for each federal agency using official eCFR API endpoints.

## Features

- Fetches regulation data directly from the official eCFR API
- Calculates the size of regulations in MB for each agency
- Uses the official eCFR agency list for accurate attribution
- Handles pagination and rate limiting
- Caches API responses for efficient processing

## Installation

1. Clone this repository
2. Install [Task](https://taskfile.dev/installation/)
3. Run the setup:
   ```bash
   task setup
   ```
   This will:
   - Create a Python virtual environment
   - Install development tools (ruff)
   - Install all dependencies

## Usage

```python
from ecfr_client import ECFRClient

# Create a client
client = ECFRClient()

# Get agency sizes in MB
agency_sizes = client.compute_agency_sizes_mb()

# Print top 10 agencies by size
for agency, info in sorted(agency_sizes.items(), 
                         key=lambda x: x[1]['mb'], 
                         reverse=True)[:10]:
    print(f"{agency}: {info['mb']:.2f} MB (titles: {info['titles']})")
```

## Common Tasks

```bash
# Format and lint code
task fmt

# Build Lambda layer (includes requests)
task layer:build

# Run Terraform (from infra/ directory)
task tf:init    # Initialize Terraform
task tf:plan    # Show planned changes
task tf:apply   # Apply changes
```

## How It Works

The package works by:
1. Fetching the official list of agencies from the eCFR API
2. For each agency, retrieving its associated CFR title and chapter references
3. Fetching the structure for each title to get the size of each chapter
4. Aggregating the sizes by agency

## Output Format

The `compute_agency_sizes_mb()` method returns a dictionary where:
- Keys are agency names (e.g., "Environmental Protection Agency")
- Values are dictionaries containing:
  - `bytes`: Total size in bytes
  - `mb`: Size in megabytes (rounded to 3 decimal places)
  - `titles`: List of CFR titles associated with the agency

## Example Output

```json
{
  "Environmental Protection Agency": {
    "bytes": 152039000,
    "mb": 152.039,
    "titles": [2, 5, 40, 41, 48]
  },
  "Department of Transportation": {
    "bytes": 12345678,
    "mb": 11.773,
    "titles": [14, 23, 49]
  }
}
```

## Configuration

Environment variables:
- `ECFR_BASE_URL`: Base URL for eCFR API (default: `https://www.ecfr.gov`)
- `ECFR_POLITE_DELAY_SECONDS`: Delay between API requests in seconds (default: `0.15`)
- `ECFR_DATE`: Date of regulations to analyze (default: `current`)

## API Endpoints Used

- Agency list: `/api/admin/v1/agencies.json`
- Title structure: `/api/versioner/v1/structure/{date}/title-{title}.json`

## Notes

- The size is calculated based on the raw text length of the regulations
- The agency list and title references come directly from the official eCFR API
- Each agency's regulations may span multiple CFR titles
- The implementation includes request caching and rate limiting to be a good API citizen

## License

MIT
