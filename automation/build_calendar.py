#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_FEED_BYTES = 5_000_000
REQUIRED_SOURCES = (("airbnb", "AIRBNB_ICAL_URL"), ("booking", "BOOKING_ICAL_URL"))


def unfold(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and output:
            output[-1] += line[1:]
        else:
            output.append(line)
    return output


def date_value(value: str) -> str | None:
    value = value.strip()
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    match = re.match(r"(\d{4})(\d{2})(\d{2})T", value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def parse_calendar(text: str, source: str) -> list[dict[str, str]]:
    if "BEGIN:VCALENDAR" not in text or "END:VCALENDAR" not in text:
        raise ValueError("invalid iCalendar feed")
    ranges: list[dict[str, str]] = []
    event: dict[str, str] | None = None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            event = {}
        elif line == "END:VEVENT" and event is not None:
            status = event.get("STATUS", "").upper()
            transparent = event.get("TRANSP", "").upper() == "TRANSPARENT"
            start = date_value(event.get("DTSTART", ""))
            end = date_value(event.get("DTEND", ""))
            if status != "CANCELLED" and not transparent and start and end and start < end:
                ranges.append({"start": start, "end": end, "source": source})
            event = None
        elif event is not None and ":" in line:
            key, value = line.split(":", 1)
            event[key.split(";", 1)[0].upper()] = value
    return ranges


def fetch_calendar(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dieppeoratoriens-calendar/2.0",
            "Accept": "text/calendar,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise ValueError("calendar feed too large")
    return data.decode("utf-8", "replace")


def merge_ranges(ranges: list[dict[str, str]]) -> list[dict[str, object]]:
    if not ranges:
        return []
    ordered = sorted(ranges, key=lambda item: (item["start"], item["end"]))
    merged: list[dict[str, object]] = []
    for item in ordered:
        if merged and item["start"] <= str(merged[-1]["end"]):
            merged[-1]["end"] = max(str(merged[-1]["end"]), item["end"])
            sources = set(merged[-1]["sources"])
            sources.add(item["source"])
            merged[-1]["sources"] = sorted(sources)
        else:
            merged.append({"start": item["start"], "end": item["end"], "sources": [item["source"]]})
    return merged


def build_payload() -> dict[str, object]:
    all_ranges: list[dict[str, str]] = []
    status: dict[str, str] = {}
    errors: list[str] = []
    for source, env_name in REQUIRED_SOURCES:
        url = os.getenv(env_name, "").strip()
        if not url:
            status[source] = "missing"
            errors.append(f"{env_name} is missing")
            continue
        try:
            text = fetch_calendar(url)
            ranges = parse_calendar(text, source)
            all_ranges.extend(ranges)
            status[source] = f"ok:{len(ranges)}"
        except Exception as exc:
            status[source] = "error"
            errors.append(f"{source}: {type(exc).__name__}")
    if errors:
        raise RuntimeError("calendar refresh aborted: " + "; ".join(errors))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "refresh_interval_minutes": 15,
        "unavailable": merge_ranges(all_ranges),
        "sources": status,
    }


def write_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(data)
        tmp = Path(handle.name)
    tmp.replace(path)


def main() -> int:
    output = Path(os.environ.get("OUTPUT", "_site/assets/data/availability.json"))
    try:
        write_atomic(output, build_payload())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
