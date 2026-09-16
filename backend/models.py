from dataclasses import dataclass, field
from datetime import date, time


@dataclass(frozen=True)
class CellModel:
    coordinate: str
    row: int
    column: int
    value: str | int | float | None
    fill_color: str | None
    is_merged: bool
    merged_range: str | None


@dataclass(frozen=True)
class GridRegion:
    id: str
    sheet_name: str
    month: int
    year: int
    day: int
    min_row: int
    max_row: int
    min_column: int
    max_column: int
    text: str
    source_cells: tuple[str, ...]
    background_color: str | None
    column_width: float | None = None


@dataclass(frozen=True)
class EventCandidate:
    id: str
    title: str | None
    date: date
    start_time: time | None
    end_time: time | None
    confidence: float
    warnings: tuple[str, ...]
    source_region_id: str
    source_sheet: str
    source_range: str
    status: str


@dataclass(frozen=True)
class SheetModel:
    title: str
    regions: tuple[GridRegion, ...]


@dataclass(frozen=True)
class WorkbookModel:
    sheets: tuple[SheetModel, ...]
