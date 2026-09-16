from datetime import date, time

from icalendar import Calendar

from backend.calendar_export import generate_ics
from backend.models import EventCandidate


def test_ics_contains_stable_uid_and_timezone():
    event = EventCandidate("event-1", "Mathématiques", date(2026, 9, 1), time(9), time(11), 1.0, (), "sheet:R1", "Planning", "S3:S3", "VALIDATED")
    first = generate_ics([event])
    second = generate_ics([event])
    first_event = next(item for item in Calendar.from_ical(first).walk() if item.name == "VEVENT")
    second_event = next(item for item in Calendar.from_ical(second).walk() if item.name == "VEVENT")
    assert first_event.get("uid") == second_event.get("uid")
    assert first_event.get("summary") == "Mathématiques"
    assert b"TZID=Europe/Paris" in first
