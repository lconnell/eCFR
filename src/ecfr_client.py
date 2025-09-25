from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


def get_date():
    return "current"
    # return "1980-07-07"


class ECFRClient:
    """JSON  client for eCFR titles.
    - Fetches per-title structure JSON (e.g.
      `/api/versioner/v1/structure/current/title-{title}.json`).
    - Extracts chapter/agency buckets using API-provided size metadata to estimate data volume.
    """

    def __init__(self):
        self.base = os.getenv("ECFR_BASE_URL", "https://www.ecfr.gov")
        # https://www.ecfr.gov/developers/documentation/api/v1
        self.structure_json_tmpl = os.getenv(
            "ECFR_STRUCTURE_JSON_PATH_TMPL",
            "/api/versioner/v1/structure/{date}/title-{title}.json",
        )
        self.user_agent = os.getenv("HTTP_USER_AGENT", "ecfr-agency-size-lambda/1.0")
        self.default_date = os.getenv("ECFR_DATE") or get_date()
        self.sleep_s = float(os.getenv("ECFR_POLITE_DELAY_SECONDS", "0.15"))

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})

    def _get(self, url, timeout=30):
        r = self._session.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _structure_url(self, title, date):
        path = self.structure_json_tmpl.format(date=date, title=title)
        return f"{self.base}{path}"

    def _available_titles(self):
        url = f"{self.base}/api/versioner/v1/titles.json"
        data = self._get(url)
        titles = []
        for info in data.get("titles", []):
            if info.get("reserved"):
                continue
            try:
                titles.append(int(info["number"]))
            except Exception:
                continue
        return sorted(titles)

    def inspect_title_structure(self, title, date=None):
        """Return the raw top-level chapter/subtitle nodes for manual inspection."""

        date = date or self.default_date
        url = self._structure_url(title, date)
        data = self._get(url)
        return data.get("children", [])

    def compute_agency_sizes_mb(self, date=None):
        date = date or self.default_date
        acc = {}
        titles_map = {}

        titles = self._available_titles()

        for t in titles:
            url = self._structure_url(t, date)
            try:
                data = self._get(url)
            except Exception as exc:  # pragma: no cover - network dependent
                logger.warning("Skipping title %s for %s: %s", t, date, exc)
                continue

            # Find chapter-like nodes; if not obvious, treat entire title as one bucket
            chapters = data.get("children", [])

            for ch in chapters:
                # Top-level nodes carry the agency in `label`/`label_description`; their `size`
                # accounts for all nested children under that chapter already, so we can treat it as
                # the total byte count for the agency slice of this title.
                label = ch.get("label") or ch.get("label_description")
                if isinstance(label, str) and label.strip():
                    agency = label.strip()
                else:
                    agency = f"Title {t} (Unattributed)"

                size = ch["size"]
                acc[agency] = acc.get(agency, 0) + int(size)
                titles_map.setdefault(agency, set()).add(t)

            time.sleep(self.sleep_s)

        # Convert to output shape
        out = {}
        for agency, b in acc.items():
            out[agency] = {
                "bytes": int(b),
                "mb": round(b / (1024 * 1024), 3),
                "titles": sorted(list(titles_map.get(agency, set()))),
            }
        return out

if __name__ == "__main__":
    client = ECFRClient()
    agencies = client.compute_agency_sizes_mb()
    print(f"Agencies collected: {len(agencies)}")

    top_agencies = sorted(
        agencies.items(),
        key=lambda item: item[1]["mb"],
        reverse=True,
    )

    for name, info in top_agencies[:10]:
        print(f"{name}: {info['mb']} MB, titles {info['titles']}")
