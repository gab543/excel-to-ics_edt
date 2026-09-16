from datetime import datetime, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from .models import EventCandidate


def generate_ics(events: tuple[EventCandidate, ...] | list[EventCandidate], timezone_name: str = "Europe/Paris") -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//edt-to-ics//EN")
    calendar.add("version", "2.0")
    zone = ZoneInfo(timezone_name)
    for candidate in events:
        if candidate.status == "IGNORED" or candidate.start_time is None or candidate.end_time is None or not candidate.title:
            continue
        item = Event()
        stable_key = "|".join([candidate.source_sheet, candidate.source_range, candidate.date.isoformat(), candidate.title])
        item.add("uid", f"{sha256(stable_key.encode('utf-8')).hexdigest()}@edt-to-ics")
        item.add("dtstamp", datetime.now(timezone.utc))
        item.add("dtstart", datetime.combine(candidate.date, candidate.start_time, zone))
        item.add("dtend", datetime.combine(candidate.date, candidate.end_time, zone))
        item.add("summary", candidate.title)
        item.add("description", f"Source Excel: {candidate.source_sheet} {candidate.source_range}")
        calendar.add_component(item)
    return calendar.to_ical()
