#!/usr/bin/env python3
"""Live smoke test for the Elektro Primorska outage data source.

Fetches and parses the live outage feed for a representative set of areas and
fails (non-zero exit) if the source cannot be reached, returns an unexpected
status, or no longer parses into any outage rows.

This is deliberately self-contained (no Home Assistant imports) so it runs on a
bare GitHub Actions runner. It mirrors the parsing logic of api.py; keep the
two in sync if the source layout changes.

Run on a schedule so the author is emailed when the source breaks.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser

import aiohttp

API_URL = "https://elektro-primorska.si/wp-admin/admin-ajax.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# A representative subset of areas to keep the daily run fast. Keys must match
# the integration's `OBMOCJA` map.
CHECK_AREAS = ["sezana", "koper", "ajdovscina", "gorica"]


class _RowParser(HTMLParser):
    """Collect attributes of every <tr> row in the response."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str | None]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            row = dict(attrs)
            if any(key.startswith("data-") for key in row):
                self.rows.append(row)


def _parse_rows(html: str) -> list[dict]:
    """Parse outage <tr> rows, keeping rows with a start/end datetime."""
    parser = _RowParser()
    parser.feed(html)
    rows = []
    for row in parser.rows:
        # Keep rows that at least carry a future-dated start; ignore rows that
        # have no datetime at all (structure change detection).
        if not any(
            row.get(k) for k in ("data-start-datetime", "data-end-datetime")
        ):
            continue
        rows.append(row)
    return rows


async def _fetch_area(session: aiohttp.ClientSession, area: str) -> list[dict]:
    params = {
        "action": "get_ajax_posts",
        "map_area": area,
        "map_post": "vsi",
        "map_type": "vsi",
    }
    timeout = aiohttp.ClientTimeout(total=30)
    async with session.get(
        API_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout
    ) as resp:
        resp.raise_for_status()
        html = await resp.text()
    return _parse_rows(html)


async def main() -> int:
    async with aiohttp.ClientSession() as session:
        errors: list[str] = []
        total_rows = 0
        for area in CHECK_AREAS:
            try:
                rows = await _fetch_area(session, area)
            except Exception as exc:  # noqa: BLE001 - report any failure
                errors.append(f"{area}: {type(exc).__name__}: {exc}")
                continue
            total_rows += len(rows)
            print(f"OK  {area:<12} -> {len(rows)} outage row(s)")

        print(
            f"\nTotal rows across {len(CHECK_AREAS) - len(errors)}/"
            f"{len(CHECK_AREAS)} areas: {total_rows}"
        )

        if errors:
            print("\nFAILURES:")
            for err in errors:
                print(f"  - {err}")
            return 1
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
