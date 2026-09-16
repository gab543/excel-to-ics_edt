from dataclasses import asdict, replace
from datetime import date, time
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .calendar_export import generate_ics
from .excel_reader import detect_events, read_workbook
from .models import EventCandidate


app = FastAPI(title="EDT to ICS")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"],)
IMPORTS: dict[str, list[EventCandidate]] = {}


def _serialize(event: EventCandidate) -> dict:
    value = asdict(event)
    value["date"] = event.date.isoformat()
    if event.start_time:
        value["start_time"] = event.start_time.isoformat()
    if event.end_time:
        value["end_time"] = event.end_time.isoformat()
    return value


class EventUpdate(BaseModel):
    title: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    status: str | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/import")
async def import_workbook(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "Veuillez fournir un fichier Excel .xlsx.")
    content = await file.read()
    with NamedTemporaryFile(suffix=".xlsx", delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        events = list(detect_events(read_workbook(temporary_path)))
    except (ValueError, KeyError) as error:
        raise HTTPException(422, "Nous n'avons pas réussi à analyser ce classeur Excel.") from error
    finally:
        temporary_path.unlink(missing_ok=True)
    import_id = str(uuid4())
    IMPORTS[import_id] = events
    return {"import_id": import_id, "events": [_serialize(event) for event in events], "warnings": sum(bool(e.warnings) for e in events)}


@app.get("/api/import/{import_id}")
def get_import(import_id: str) -> dict:
    events = IMPORTS.get(import_id)
    if events is None:
        raise HTTPException(404, "Import introuvable.")
    return {"import_id": import_id, "events": [_serialize(event) for event in events]}


@app.put("/api/import/{import_id}/events/{event_id}")
def update_event(import_id: str, event_id: str, update: EventUpdate) -> dict:
    events = IMPORTS.get(import_id)
    if events is None:
        raise HTTPException(404, "Import introuvable.")
    for index, event in enumerate(events):
        if event.id == event_id:
            values = update.model_dump(exclude_unset=True)
            for field_name, converter in (("date", date.fromisoformat), ("start_time", time.fromisoformat), ("end_time", time.fromisoformat)):
                if values.get(field_name) is not None:
                    try:
                        values[field_name] = converter(values[field_name])
                    except ValueError as error:
                        raise HTTPException(422, f"Valeur invalide pour {field_name}.") from error
            updated = replace(event, **values)
            events[index] = updated
            return _serialize(updated)
    raise HTTPException(404, "Événement introuvable.")


@app.post("/api/import/{import_id}/export")
def export_import(import_id: str) -> Response:
    events = IMPORTS.get(import_id)
    if events is None:
        raise HTTPException(404, "Import introuvable.")
    first_sheet = next((event.source_sheet for event in events), None)
    exportable_events = [event for event in events if event.source_sheet == first_sheet]
    incomplete = [
        event for event in exportable_events
        if event.status != "IGNORED"
        and (event.start_time is None or event.end_time is None or not event.title)
    ]
    return Response(
        generate_ics(exportable_events),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=planning.ics",
            "X-EDT-Excluded-Events": str(len(incomplete)),
            "X-EDT-Exported-Sheet": first_sheet or "",
        },
    )
