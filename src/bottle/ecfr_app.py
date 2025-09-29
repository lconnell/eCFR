#!/usr/bin/env python3.12
"""
Simplified eCFR Agency Size Tracker using Bottle Framework
A local web application that fetches and displays eCFR agency sizes.
"""

# Standard library imports
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import requests

from bottle import TEMPLATE_PATH, Bottle, redirect, request, run, static_file, template

app = Bottle()

# Set template directory
template_dir = str(Path(__file__).parent / "templates")
TEMPLATE_PATH.insert(0, template_dir)
app.template_path = [template_dir]
app.config["TEMPLATE_PATH"] = template_dir

# Configuration
DATA_FILE = Path(__file__).parent / "agency_sizes.json"
ECFR_BASE_URL = "https://www.ecfr.gov"
USER_AGENT = "ecfr-agency-size-local/1.0"


class SimpleECFRClient:
    """Simplified eCFR client for local use."""

    def __init__(self):
        self.base = ECFR_BASE_URL
        self.user_agent = USER_AGENT
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _get(self, url, timeout=30):
        """Make HTTP GET request with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _get_agencies_url(self):
        return f"{self.base}/api/admin/v1/agencies.json"

    def _get_structure_url(self, title):
        return f"{self.base}/api/versioner/v1/structure/current/title-{title}.json"

    def _find_chapter_size(self, structure, chapter_identifier):
        """Recursively find chapter size in structure."""
        if not structure:
            return None

        stack = [structure]
        while stack:
            node = stack.pop()
            if node.get("identifier", "").strip() == chapter_identifier:
                return node.get("size")
            for child in node.get("children") or []:
                stack.append(child)
        return None

    def compute_agency_sizes_mb(self):
        """Compute sizes for all agencies."""
        print("Fetching agencies...")
        agencies_url = self._get_agencies_url()
        agencies_data = self._get(agencies_url)

        if not agencies_data:
            return {}

        sizes = defaultdict(int)
        titles_map = defaultdict(set)

        for agency in agencies_data.get("agencies", []):
            name = agency.get("name")
            if not name:
                continue

            print(f"Processing {name}...")

            for ref in agency.get("cfr_references", []):
                title = ref.get("title")
                chapter = ref.get("chapter")

                if title is None or chapter is None:
                    continue

                # Fetch title structure
                structure_url = self._get_structure_url(title)
                structure = self._get(structure_url)

                if not structure:
                    continue

                # Find chapter size
                chapter_size = self._find_chapter_size(structure, chapter)
                if chapter_size is None:
                    continue

                sizes[name] += int(chapter_size)
                titles_map[name].add(int(title))

            # Be polite to the API
            time.sleep(0.15)

        # Convert to output format
        result = {}
        for agency, total_bytes in sizes.items():
            result[agency] = {
                "bytes": total_bytes,
                "mb": round(total_bytes / (1024 * 1024), 3),
                "titles": len(titles_map[agency]),
            }

        return result


def load_cached_data():
    """Load cached agency data from local file."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cached data: {e}")
    return None


def save_data_to_file(data):
    """Save agency data to local file."""
    try:
        DATA_FILE.parent.mkdir(exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def refresh_data():
    """Fetch fresh data from eCFR API."""
    print("Refreshing data from eCFR API...")
    client = SimpleECFRClient()
    sizes = client.compute_agency_sizes_mb()

    if not sizes:
        return None

    now = datetime.now(timezone.utc).isoformat()
    data = {
        "updated_at": now,
        "source": "eCFR",
        "units": "MB (approx, text length based)",
        "agencies": sizes,
    }

    if save_data_to_file(data):
        print(f"Data refreshed successfully. {len(sizes)} agencies processed.")
        return data
    return None


@app.route("/")
def index():
    """Main page with agency data."""
    data = load_cached_data()

    if not data:
        # No cached data, try to refresh
        data = refresh_data()
        if not data:
            return template("error")

    # Process data for display
    agencies = data.get("agencies", {})
    sort_by = request.query.get("sort", "size")

    if sort_by == "name":
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[0]))
    elif sort_by == "size_asc":
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[1]["mb"]))
    else:  # size_desc
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[1]["mb"], reverse=True))

    # Format the last updated time
    updated_at = data.get("updated_at", "Unknown")
    if updated_at != "Unknown":
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            updated_at = dt.strftime("%B %d, %Y at %I:%M %p %Z")
        except (ValueError, AttributeError):
            pass

    # Render the template with the data
    return template(
        "index", updated_at=updated_at, data=data, sort_by=sort_by, agencies=sorted_agencies
    )


@app.route("/api/agencies")
def api_agencies():
    """JSON API endpoint for agency data."""
    data = load_cached_data()

    if not data:
        return {"error": "Data not available. Try refreshing."}

    agencies = data.get("agencies", {})
    sort_by = request.query.get("sort", "size")

    # Sort agencies based on query parameter
    if sort_by == "name":
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[0]))
    elif sort_by == "size_asc":
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[1]["mb"]))
    else:  # size_desc
        sorted_agencies = dict(sorted(agencies.items(), key=lambda x: x[1]["mb"], reverse=True))

    return {
        "updated_at": data.get("updated_at"),
        "source": data.get("source"),
        "units": data.get("units"),
        "agencies": sorted_agencies,
    }


@app.route("/refresh", method="POST")
def do_refresh():
    """Refresh data from eCFR API."""
    data = refresh_data()
    if data:
        return redirect("/")
    else:
        return redirect("/?error=refresh_failed")


@app.route("/static/<filename>")
def serve_static(filename):
    """Serve static files."""
    return static_file(filename, root=Path(__file__).parent / "static")


def find_available_port(start_port=8080, max_attempts=10):
    # """Find an available port starting from start_port."""
    # import socket  # Imported here to avoid unused import at module level

    # for port in range(start_port, start_port + max_attempts):
    #     try:
    #         with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
    #             s.bind(("localhost", port))
    #             return port
    #     except OSError:
    #         continue
    # return start_port
    return 8080


if __name__ == "__main__":
    port = 8080
    print(f"Starting eCFR Agency Size Tracker on port {port}...")
    print(f"Open http://localhost:{port} in your browser")

    # Try to load existing data or create initial data
    if not load_cached_data():
        print("No cached data found. Fetching initial data...")
        refresh_data()

    # Start the web server
    run(app, host="localhost", port=port, debug=True)
