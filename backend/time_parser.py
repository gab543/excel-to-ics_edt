import re
from datetime import time


TIME_RE = re.compile(r"(?P<hour>\d{1,2})\s*(?:h|:)\s*(?P<minute>\d{2})?", re.IGNORECASE)
RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}\s*(?:h|:)\s*(?:\d{2})?)\s*[-–]\s*"
    r"(?P<end>\d{1,2}\s*(?:h|:)\s*(?:\d{2})?)",
    re.IGNORECASE,
)
OPEN_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}\s*(?:h|:)\s*(?:\d{2})?)\s*[-–]\s*(?:\.\.\.|…)",
    re.IGNORECASE,
)


def parse_time(value: str) -> time | None:
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        return None
    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)


def parse_time_range(value: str) -> tuple[time | None, time | None]:
    match = RANGE_RE.search(value.replace(" ’", " "))
    if match:
        return parse_time(match.group("start")), parse_time(match.group("end"))
    open_match = OPEN_RANGE_RE.search(value.replace(" ’", " "))
    return (parse_time(open_match.group("start")), None) if open_match else (None, None)


def find_time_ranges(value: str) -> list[tuple[time | None, time | None, int, int]]:
    ranges = []
    occupied: list[tuple[int, int]] = []
    for match in RANGE_RE.finditer(value.replace(" ’", " ")):
        start = parse_time(match.group("start"))
        end = parse_time(match.group("end"))
        if start is not None and end is not None:
            ranges.append((start, end, match.start(), match.end()))
            occupied.append((match.start(), match.end()))
    for match in OPEN_RANGE_RE.finditer(value.replace(" ’", " ")):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        start = parse_time(match.group("start"))
        if start is not None:
            ranges.append((start, None, match.start(), match.end()))
    ranges.sort(key=lambda item: item[2])
    return ranges
