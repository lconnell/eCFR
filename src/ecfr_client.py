import logging
import os
import time
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)


def get_date():
    return "current"


class ECFRClient:
    """JSON client for eCFR titles."""

    def __init__(self):
        self.base = os.getenv("ECFR_BASE_URL", "https://www.ecfr.gov")
        self.structure_json_tmpl = os.getenv(
            "ECFR_TITLE_JSON_PATH_TMPL",
            "/api/versioner/v1/structure/{date}/title-{title}.json",
        )
        self.agencies_path = os.getenv(
            "ECFR_AGENCIES_PATH",
            "/api/admin/v1/agencies",
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

    def _agencies_url(self):
        return f"{self.base}{self.agencies_path}.json"

    def _iter_agencies(self):
        url = self._agencies_url()
        data = self._get(url)
        for agency in data.get("agencies", []):
            yield agency

    def _fetch_title_structure(self, title, date):
        url = self._structure_url(title, date)
        return self._get(url)

    def _find_chapter_size(self, structure, chapter_identifier):
        stack = [structure]
        chapter_identifier = (chapter_identifier or "").strip()
        while stack:
            node = stack.pop()
            if node.get("identifier", "").strip() == chapter_identifier:
                return node.get("size")
            for child in node.get("children") or []:
                stack.append(child)
        return None

    def compute_agency_sizes_mb(self, date=None):
        date = date or self.default_date
        sizes = defaultdict(int)
        titles_map = defaultdict(set)
        structure_cache = {}

        for agency in self._iter_agencies():
            name = agency.get("name")
            if not name:
                continue

            for ref in agency.get("cfr_references", []):
                title = ref.get("title")
                chapter = ref.get("chapter")
                if title is None or chapter is None:
                    continue

                if title not in structure_cache:
                    try:
                        structure_cache[title] = self._fetch_title_structure(title, date)
                    except Exception as exc:  # pragma: no cover - network dependent
                        logger.warning("Skipping title %s for %s: %s", title, date, exc)
                        structure_cache[title] = None
                        continue
                    time.sleep(self.sleep_s)

                structure = structure_cache.get(title)
                if not structure:
                    continue

                chapter_size = self._find_chapter_size(structure, chapter)
                if chapter_size is None:
                    continue

                sizes[name] += int(chapter_size)
                titles_map[name].add(int(title))

        out = {}
        for agency, total_bytes in sizes.items():
            out[agency] = {
                "bytes": total_bytes,
                "mb": round(total_bytes / (1024 * 1024), 3),
                "titles": len(titles_map[agency]),
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
        print(f"{name}: {info['mb']} MB, {info['titles']} titles")
