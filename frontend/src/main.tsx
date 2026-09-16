import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import frLocale from "@fullcalendar/core/locales/fr";
import "./styles.css";

type EventItem = {
  id: string;
  title: string | null;
  date: string;
  start_time: string | null;
  end_time: string | null;
  confidence: number;
  warnings: string[];
  source_sheet: string;
  source_range: string;
  status: string;
};

const API = "/api";

async function readJson(response: Response): Promise<Record<string, any>> {
  const text = await response.text();
  if (!text.trim()) {
    throw new Error(`Le serveur a renvoyé une réponse vide (${response.status}).`);
  }
  try {
    return JSON.parse(text) as Record<string, any>;
  } catch {
    throw new Error(`Le serveur a renvoyé une réponse invalide (${response.status}).`);
  }
}

function needsReview(event: EventItem): boolean {
  return event.warnings.length > 0 && event.status !== "VALIDATED" && event.status !== "IGNORED";
}

function App() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [importId, setImportId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>("all");

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(`${API}/import`, { method: "POST", body });
      const data = await readJson(response);
      if (!response.ok) throw new Error(data.detail ?? "Import impossible.");
      setImportId(data.import_id);
      setEvents(data.events);
      setSelectedSheet(data.events[0]?.source_sheet ?? "all");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Import impossible.");
    } finally {
      setBusy(false);
    }
  }

  async function exportIcs() {
    if (!importId) return;
    const response = await fetch(`${API}/import/${importId}/export`, { method: "POST" });
    if (!response.ok) {
      const data = await readJson(response);
      setError(data.detail);
      return;
    }
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "planning.ics";
    link.click();
    URL.revokeObjectURL(link.href);
    const excluded = response.headers.get("X-EDT-Excluded-Events");
    setError(excluded && Number(excluded) > 0
      ? `${excluded} événement(s) incomplet(s) n'ont pas été inclus dans le fichier ICS.`
      : null);
  }

  async function updateStatus(event: EventItem, status: "VALIDATED" | "IGNORED") {
    if (!importId) return;
    setError(null);
    try {
      const response = await fetch(`${API}/import/${importId}/events/${event.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      const data = await readJson(response);
      if (!response.ok) throw new Error(data.detail ?? "Mise à jour impossible.");
      setEvents((current) => current.map((item) => item.id === event.id ? { ...item, status: data.status } : item));
      setSelectedEvent((current) => current?.id === event.id ? { ...current, status: data.status } : current);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Mise à jour impossible.");
    }
  }

  const warnings = events.filter(needsReview).length;
  const sheets = [...new Set(events.map((event) => event.source_sheet))];
  const visibleEvents = selectedSheet === "all" ? events : events.filter((event) => event.source_sheet === selectedSheet);
  const visibleWarnings = visibleEvents.filter(needsReview).length;
  const calendarEvents = visibleEvents.map((event) => ({
    id: event.id,
    title: event.title ?? "Événement sans titre",
    start: event.start_time ? `${event.date}T${event.start_time}` : event.date,
    end: event.start_time && event.end_time ? `${event.date}T${event.end_time}` : undefined,
    allDay: !event.start_time || !event.end_time,
    className: event.warnings.length > 0 ? "calendar-event-review" : "calendar-event-ready",
  }));

  return (
    <main>
      <header>
        <p className="kicker">CALENDRIER PERSONNEL</p>
        <h1>Votre emploi du temps,<br /><em>enfin lisible.</em></h1>
        <p className="lede">Déposez un classeur Excel. Les cellules fusionnées, les semaines irrégulières et les ambiguïtés restent visibles jusqu'à votre validation.</p>
      </header>
      <section className="upload-panel">
        <label className="dropzone">
          <span className="upload-icon">↑</span>
          <strong>{busy ? "Analyse en cours..." : "Déposer le classeur Excel"}</strong>
          <span>Format .xlsx uniquement</span>
          <input type="file" accept=".xlsx" disabled={busy} onChange={(event) => event.target.files?.[0] && upload(event.target.files[0])} />
        </label>
        {error && <p className="error">{error}</p>}
      </section>
      {events.length > 0 && (
        <section className="results">
          <div className="results-heading">
            <div><p className="kicker">ANALYSE TERMINÉE</p><h2>{visibleEvents.length} événements affichés</h2></div>
            <button onClick={exportIcs}>Exporter la première feuille <span>↓</span></button>
          </div>
          <div className="stats"><span><b>{visibleEvents.length - visibleWarnings}</b> fiables</span><span className={visibleWarnings ? "warn" : ""}><b>{visibleWarnings}</b> à vérifier</span></div>
          <div className="calendar-controls">
            <label htmlFor="sheet-filter">Agenda affiché</label>
            <select id="sheet-filter" value={selectedSheet} onChange={(event) => { setSelectedSheet(event.target.value); setSelectedEvent(null); }}>
              <option value="all">Tous les cursus</option>
              {sheets.map((sheet) => <option value={sheet} key={sheet}>{sheet}</option>)}
            </select>
            <span>{visibleEvents.length} événement{visibleEvents.length === 1 ? "" : "s"} dans cette vue</span>
          </div>
          <div className="calendar-shell">
            <FullCalendar
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView="timeGridWeek"
              initialDate={visibleEvents[0]?.date}
              locale={frLocale}
              firstDay={1}
              weekends
              height="auto"
              nowIndicator
              slotEventOverlap={false}
              headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth,timeGridWeek,timeGridDay" }}
              events={calendarEvents}
              eventClick={(info) => setSelectedEvent(events.find((event) => event.id === info.event.id) ?? null)}
            />
          </div>
          {selectedEvent && <aside className="event-detail"><div><p className="kicker">DÉTAIL DE L'ÉVÉNEMENT</p><h3>{selectedEvent.title ?? "Événement sans titre"}</h3><p>{selectedEvent.date} · {selectedEvent.start_time ?? "heure inconnue"}{selectedEvent.end_time ? ` → ${selectedEvent.end_time}` : ""}</p><small>Source : {selectedEvent.source_sheet} · {selectedEvent.source_range}</small>{selectedEvent.warnings.map((warning) => <p className="warn" key={warning}>⚠ {warning}</p>)}{needsReview(selectedEvent) && <div className="review-actions"><button onClick={() => updateStatus(selectedEvent, "VALIDATED")}>Valider</button><button className="secondary-action" onClick={() => updateStatus(selectedEvent, "IGNORED")}>Ignorer</button></div>}{selectedEvent.status === "VALIDATED" && <p className="status-ok">Événement validé</p>}{selectedEvent.status === "IGNORED" && <p className="status-muted">Événement ignoré</p>}</div><button className="close-detail" onClick={() => setSelectedEvent(null)} aria-label="Fermer">×</button></aside>}
          <section className="review-queue"><div className="review-heading"><div><p className="kicker">VÉRIFICATION</p><h3>{visibleWarnings} événement{visibleWarnings === 1 ? "" : "s"} à contrôler</h3></div><span>Cliquez sur un événement du calendrier pour le traiter.</span></div>{visibleEvents.filter(needsReview).slice(0, 20).map((event) => <button className="review-item" key={event.id} onClick={() => setSelectedEvent(event)}><span><strong>{event.title ?? "Événement sans titre"}</strong><small>{event.date} · {event.start_time ?? "heure inconnue"} · {event.source_sheet}</small></span><b>Vérifier</b></button>)}{visibleWarnings === 0 && <p className="status-ok">Tous les événements visibles ont été vérifiés.</p>}</section>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
