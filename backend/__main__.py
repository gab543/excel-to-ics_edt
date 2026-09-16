from pathlib import Path

from .excel_reader import detect_events, read_workbook


if __name__ == "__main__":
    workbook = next(Path(__file__).parents[1].glob("*.xlsx"))
    events = detect_events(read_workbook(workbook))
    print(f"{len(events)} événements détectés")
