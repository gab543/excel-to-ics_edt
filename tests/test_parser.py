from datetime import time
from pathlib import Path

from backend.excel_reader import detect_events, read_workbook
from backend.models import GridRegion, SheetModel, WorkbookModel
from backend.time_parser import parse_time, parse_time_range


WORKBOOK = next(Path(__file__).parents[1].glob("*.xlsx"))


def test_parse_supported_time_formats():
    assert parse_time("7h30") == time(7, 30)
    assert parse_time("07:00") == time(7, 0)
    assert parse_time_range("8h45 - 10h45") == (time(8, 45), time(10, 45))


def test_real_workbook_exposes_sheets_and_merged_regions():
    model = read_workbook(WORKBOOK)
    assert len(model.sheets) == 4
    assert all(sheet.regions for sheet in model.sheets)
    assert any(len(region.source_cells) > 1 for sheet in model.sheets for region in sheet.regions)


def test_real_workbook_produces_events_with_sources_and_warnings():
    events = detect_events(read_workbook(WORKBOOK))
    assert len(events) > 100
    assert not any(event.title == "50" for event in events)
    assert all(event.source_sheet and event.source_range for event in events)
    assert any(event.warnings for event in events)
    assert any(event.start_time and event.end_time for event in events)


def test_multiple_time_ranges_are_detected_without_format_specific_rules():
    region = GridRegion(
        id="Test:R1",
        sheet_name="Test",
        month=9,
        year=2026,
        day=16,
        min_row=1,
        max_row=1,
        min_column=1,
        max_column=1,
        text="Atelier polyvalent\n09h-10h\nGroupe matin\n14h30-16h",
        source_cells=("A1",),
        background_color=None,
    )
    events = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))
    assert [(event.start_time, event.end_time) for event in events] == [
        (time(9, 0), time(10, 0)),
        (time(14, 30), time(16, 0)),
    ]


def test_missing_end_time_defaults_to_end_of_day():
    region = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Cours 14h30-...", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert event.start_time == time(14, 30)
    assert event.end_time == time(18)
    assert event.warnings == ()
    assert event.status == "DETECTED"


def test_unknown_activity_after_lunch_pause_uses_afternoon_bounds():
    activity = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 4, 4, "Sport / activités personnelles", ("D1",), None)
    pause = GridRegion("Test:R2", "Test", 9, 2026, 16, 1, 1, 3, 3, "Temps de pause", ("C1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (activity, pause)),)))[0]
    assert event.start_time == time(14)
    assert event.end_time == time(18)
    assert event.warnings == ()
    assert event.status == "DETECTED"


def test_unknown_activity_after_morning_and_afternoon_marker_uses_afternoon_bounds():
    morning = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Cours 8h45-13h", ("A1",), None)
    marker = GridRegion("Test:R2", "Test", 9, 2026, 16, 1, 1, 2, 2, "Séminaire après-midi", ("B1",), None)
    activity = GridRegion("Test:R3", "Test", 9, 2026, 16, 1, 1, 3, 3, "Activité personnelle", ("C1",), None)
    events = detect_events(WorkbookModel((SheetModel("Test", (morning, marker, activity)),)))
    assert events[-1].start_time == time(14)
    assert events[-1].end_time == time(18)
    assert events[-1].warnings == ()
    assert events[-1].status == "DETECTED"


def test_unknown_activity_ends_at_first_known_afternoon_activity():
    morning = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Cours 11h-13h", ("A1",), None)
    pause = GridRegion("Test:R2", "Test", 9, 2026, 16, 1, 1, 2, 2, "Temps de pause", ("B1",), None)
    activity = GridRegion("Test:R3", "Test", 9, 2026, 16, 1, 1, 3, 3, "Activité personnelle", ("C1",), None)
    afternoon = GridRegion("Test:R4", "Test", 9, 2026, 16, 1, 1, 4, 4, "Cours 16h-18h", ("D1",), None)
    events = detect_events(WorkbookModel((SheetModel("Test", (morning, pause, activity, afternoon)),)))
    inferred = events[0] if events[0].title == "Activité personnelle" else events[1]
    assert inferred.start_time == time(14)
    assert inferred.end_time == time(16)
    assert inferred.warnings == ()


def test_narrow_activity_uses_lunch_pause_slot_before_afternoon_activity():
    morning = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Cours 11h-13h", ("A1",), None, 25.0)
    narrow_activity = GridRegion("Test:R2", "Test", 9, 2026, 16, 1, 1, 2, 2, "Séminaire après-midi", ("B1",), None, 9.0)
    afternoon = GridRegion("Test:R3", "Test", 9, 2026, 16, 1, 1, 3, 3, "Sport / activités personnelles", ("C1",), None, 25.0)
    events = detect_events(WorkbookModel((SheetModel("Test", (morning, narrow_activity, afternoon)),)))
    seminar = next(event for event in events if event.title == "Séminaire après-midi")
    sport = next(event for event in events if event.title == "Sport / activités personnelles")
    assert (seminar.start_time, seminar.end_time) == (time(13), time(14))
    assert (sport.start_time, sport.end_time) == (time(14), time(18))
    assert seminar.warnings == ()


def test_saturday_events_are_ignored():
    saturday = GridRegion("Test:R1", "Test", 11, 2026, 7, 1, 1, 1, 1, "Cours 09h-11h", ("A1",), None)
    events = detect_events(WorkbookModel((SheetModel("Test", (saturday,)),)))
    assert events == ()


def test_day_word_fills_missing_bounds_with_full_day():
    region = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Journée d'accueil", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert (event.start_time, event.end_time) == (time(8, 45), time(18))
    assert event.warnings == ()
    assert event.status == "DETECTED"


def test_day_word_only_overrides_incomplete_ranges():
    region = GridRegion("Test:R1", "Test", 9, 2026, 16, 1, 1, 1, 1, "Jour de rentrée 14h-...", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert (event.start_time, event.end_time) == (time(8, 45), time(18))


def test_holiday_event_is_assumed_full_day():
    region = GridRegion("Test:R1", "Test", 11, 2026, 11, 1, 1, 1, 1, "FÉRIÉ Armistice", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert (event.start_time, event.end_time) == (time(8, 45), time(18))
    assert event.warnings == ()


def test_excel_holiday_spelling_with_final_accent_is_assumed_full_day():
    region = GridRegion("Test:R1", "Test", 11, 2026, 1, 1, 1, 1, 1, "FERIÉ TOUSSAINT", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert (event.start_time, event.end_time) == (time(8, 45), time(18))
    assert event.warnings == ()


def test_single_time_line_keeps_the_following_event_name():
    region = GridRegion("Test:R1", "Test", 10, 2026, 13, 1, 1, 1, 1, "13h\nleçcons du mardi", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert event.title == "13h leçcons du mardi"


def test_week_marker_with_missing_hours_is_assumed_full_day():
    region = GridRegion("Test:R1", "Test", 8, 2026, 31, 1, 1, 1, 1, "Semaine introductive", ("A1",), None)
    event = detect_events(WorkbookModel((SheetModel("Test", (region,)),)))[0]
    assert (event.start_time, event.end_time) == (time(8, 45), time(18))
    assert event.warnings == ()
