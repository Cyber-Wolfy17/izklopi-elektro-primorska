"""API client for Elektro Primorska planned outages."""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import aiohttp

from .const import API_URL, DATETIME_FORMAT, TIMEZONE

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


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


def _parse_datetime(value: str | None, tz: ZoneInfo) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, DATETIME_FORMAT).replace(tzinfo=tz)
    except ValueError:
        return None


def normalize_house_number(value: str | None) -> str:
    """Normalize a house number: lowercase, no whitespace ('11 A' -> '11a')."""
    return "".join((value or "").lower().split())


def parse_outages(html: str, now: datetime | None = None) -> list[dict]:
    """Parse outage rows from the ajax response.

    Outages that already ended are dropped (same behaviour as the original
    script).
    """
    tz = ZoneInfo(TIMEZONE)
    if now is None:
        now = datetime.now(tz)

    parser = _RowParser()
    parser.feed(html)

    outages: list[dict] = []
    for row in parser.rows:
        start = _parse_datetime(row.get("data-start-datetime"), tz)
        end = _parse_datetime(row.get("data-end-datetime"), tz)
        if end is not None and end < now:
            continue
        outages.append(
            {
                "akcija": (row.get("data-tip-naziv") or "").strip(),
                "lokacija": (row.get("data-ulica-naziv") or "").strip(),
                "kraj": (row.get("data-kraj") or "").strip(),
                "hisne_stevilke": (row.get("data-ulica-stevilke") or "").strip(),
                "od": start,
                "do": end,
            }
        )
    return outages


def filter_outages(
    outages: list[dict], kraj: str, hisna_stevilka: str | None = None
) -> list[dict]:
    """Filter outages matching kraj and optionally the house number.

    Kraj is matched as a substring of the place name or street name (same as
    the original script). The house number, when set, must exactly match one
    of the listed house numbers (normalized); outages without a house-number
    list are kept because they typically affect the whole area.
    """
    kraj_lower = kraj.strip().lower()
    hisna = normalize_house_number(hisna_stevilka)

    def matches(outage: dict) -> bool:
        if (
            kraj_lower not in outage["lokacija"].lower()
            and kraj_lower not in outage["kraj"].lower()
        ):
            return False
        if not hisna:
            return True
        stevilke = [
            normalize_house_number(s)
            for s in outage["hisne_stevilke"].split(",")
            if s.strip()
        ]
        if not stevilke:
            return True
        return hisna in stevilke

    matched = [o for o in outages if matches(o)]
    matched.sort(
        key=lambda o: (
            o["od"] is None,
            o["od"] or datetime.max.replace(tzinfo=timezone.utc),
        )
    )
    return matched


class ElektroIzpadiClient:
    """Async client for the Elektro Primorska outage endpoint."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_fetch_outages(self, obmocje: str) -> list[dict]:
        """Fetch and parse all outages for the given area."""
        params = {
            "action": "get_ajax_posts",
            "map_area": obmocje,
            "map_post": "vsi",
            "map_type": "vsi",
        }
        headers = {"User-Agent": USER_AGENT}
        timeout = aiohttp.ClientTimeout(total=30)
        async with self._session.get(
            API_URL, params=params, headers=headers, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            html = await resp.text()
        return parse_outages(html)
