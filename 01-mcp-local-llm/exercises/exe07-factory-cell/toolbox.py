"""Every MCP capability EXE07 can offer. ``exe07.py`` chooses which ones to register.

Three families of tools, one resource, one prompt:

- raw log tools:      describe_cell, get_log, read_log_page
- task-shaped tools:  production_summary, part_history
- swiss army knife:   describe, query, count, check_quotes
- resource:           cell://glossary  (the host attaches it)
- prompt:             investigate_rejects  (the host builds the user message from it)
"""

import re
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from factory import Factory
from factory.config import hhmm, parse_hhmm
from factory.logbook import LogLine

LINES_PER_PAGE = 100
MAX_LINES = 150

factory: Factory


def load(recipe: Path) -> Factory:
    """Simulate the recipe; every tool reads the logs of this run."""
    global factory
    factory = Factory.from_yaml(recipe).run()
    return factory


MilitaryTime = Annotated[
    str,
    Field(pattern=r"^([01][0-9]|2[0-3])[0-5][0-9]$", description="Military time HHMM, e.g. '0930'."),
]


# --- helpers ---------------------------------------------------------------


def production_ids() -> list[str]:
    return [p.id for p in factory.recipe.productions]


def check_production(production: str | None) -> None:
    if production is not None and production not in production_ids():
        raise ToolError(f"Unknown production: {production}. Productions: {', '.join(production_ids())}")


def check_station(station: str | None) -> None:
    if station is not None and station not in factory.stations:
        raise ToolError(f"Unknown station: {station}. Stations: {', '.join(factory.stations)}")


def pages(production: str, station: str) -> list[list[str]]:
    lines = factory.logbook.text(station, production)
    return [lines[i:i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[]]


def glossary_text(station_ids: Sequence[str] | None = None) -> str:
    blocks = []
    for station_id in station_ids or factory.stations:
        station = factory.stations[station_id]
        doc = (type(station).__doc__ or "").strip().splitlines()[0]
        lines = [f"{station_id} ({station.type_name}): {doc}"]
        lines += [f"  {event}: {meaning}" for event, meaning in station.events.items()]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# --- raw log tools -----------------------------------------------------------


class StationInfo(BaseModel):
    id: str
    type: str
    description: str
    events: list[str]


class ProductionInfo(BaseModel):
    id: str
    start: str
    end: str
    parts: int
    log_pages: dict[str, int]


class CellInfo(BaseModel):
    route: list[str]
    part_tolerance: str
    stations: list[StationInfo]
    productions: list[ProductionInfo]


class LogPage(BaseModel):
    production: str
    station: str
    page: int
    total_pages: int
    lines: str


class LogRange(BaseModel):
    production: str
    station: str
    start: str
    end: str
    line_count: int
    truncated: bool
    next_start: str | None
    lines: str


def describe_cell() -> CellInfo:
    """Describe the production cell: route of the parts, stations and the events they
    log, and the production orders with their hours and log sizes.
    Call this first."""
    recipe = factory.recipe
    return CellInfo(
        route=recipe.route,
        part_tolerance=f"{recipe.part.nominal_mm:.3f} mm +/- {recipe.part.tolerance_mm:.3f} mm",
        stations=[
            StationInfo(
                id=station_id,
                type=station.type_name,
                description=(type(station).__doc__ or "").strip().splitlines()[0],
                events=sorted({line.event for line in factory.logbook.lines(station_id)}),
            )
            for station_id, station in factory.stations.items()
        ],
        productions=[
            ProductionInfo(
                id=p.id,
                start=hhmm(p.start),
                end=hhmm(p.end),
                parts=p.orders.count,
                log_pages={station_id: len(pages(p.id, station_id)) for station_id in factory.stations},
            )
            for p in recipe.productions
        ],
    )


def get_log(production: str, station: str, start: MilitaryTime, end: MilitaryTime) -> LogRange:
    """Read what a station logged during one production between two times
    (start included, end excluded).

    At most 150 lines are returned. If the range holds more, truncated is true and
    next_start tells where to continue.

    Args:
        production: Production id from describe_cell, for example 'PO-1001'.
        station: Station id from describe_cell, for example 'WH1'.
        start: First minute, military time, for example '0900'.
        end: Minute after the last one, military time, for example '1000'.
    """
    check_production(production)
    check_station(station)
    first, last = parse_hhmm(start), parse_hhmm(end)
    if last <= first:
        raise ToolError("end must be after start.")
    lines = factory.logbook.lines(station, production, first, last)
    shown, next_start = lines, None
    if len(lines) > MAX_LINES:
        # Stop before the minute of the first line left out, so that
        # continuing from next_start neither skips nor repeats lines.
        cut = lines[MAX_LINES].t.replace(second=0)
        shown = [line for line in lines[:MAX_LINES] if line.t < cut]
        next_start = hhmm(cut.time())
    return LogRange(
        production=production,
        station=station,
        start=start,
        end=end,
        line_count=len(shown),
        truncated=next_start is not None,
        next_start=next_start,
        lines="\n".join(line.text() for line in shown),
    )


def read_log_page(production: str, station: str, page: int = 1) -> LogPage:
    """Read one page (100 lines) of a station's log for one production, oldest first.

    Prefer get_log when you know which hours matter.

    Args:
        production: Production id from describe_cell, for example 'PO-1001'.
        station: Station id from describe_cell, for example 'WH1'.
        page: Page number, starting at 1. describe_cell tells how many pages exist.
    """
    check_production(production)
    check_station(station)
    all_pages = pages(production, station)
    if not 1 <= page <= len(all_pages):
        raise ToolError(f"{station} in {production} has pages 1 to {len(all_pages)}.")
    return LogPage(
        production=production,
        station=station,
        page=page,
        total_pages=len(all_pages),
        lines="\n".join(all_pages[page - 1]),
    )


# --- task-shaped tools ---------------------------------------------------------


class ProductionSummary(BaseModel):
    production: str
    released: int
    stored: int
    rejected_at_final_gauge: list[str]
    scrapped_at_vision: list[str]
    unfinished: list[str]


def production_summary(production: str) -> ProductionSummary:
    """Summarize one production order: how many parts were stored, and the ids of the
    parts rejected by the final gauge, scrapped by the camera, or not finished.

    Args:
        production: Production id, for example 'PO-1001'.
    """
    check_production(production)
    parts = [p for p in factory.parts if p.production == production]
    return ProductionSummary(
        production=production,
        released=len(parts),
        stored=sum(p.status == "stored" for p in parts),
        rejected_at_final_gauge=[p.id for p in parts if p.status == "rejected"],
        scrapped_at_vision=[p.id for p in parts if p.status == "scrapped"],
        unfinished=[p.id for p in parts if p.status == "in_progress"],
    )


class PartHistory(BaseModel):
    part: str
    production: str
    lines: str


def part_history(part: str) -> PartHistory:
    """Every log line about one part, from every station, in time order:
    where it went, which machine and tool worked on it, how it ended.

    Args:
        part: Part id, for example 'P-0301'.
    """
    lines = [line for line in factory.logbook.lines() if line.part == part]
    if not lines:
        raise ToolError(f"No log line mentions part {part}. Part ids look like 'P-0301'.")
    return PartHistory(part=part, production=lines[0].production,
                       lines="\n".join(line.text() for line in lines))


# --- swiss army knife ------------------------------------------------------------


def describe(topic: str = "cell") -> str:
    """Documentation on demand. topic='cell' gives the route, the stations and the
    productions (the latest is marked). A station id (e.g. 'WH1') explains what that
    station does and what each of its events and fields means. An event name
    (e.g. 'GAUGE') explains that event.

    Args:
        topic: 'cell', a station id, or an event name.
    """
    recipe = factory.recipe
    if topic == "cell":
        latest = recipe.productions[-1].id
        productions = "\n".join(
            f"  {p.id}: {hhmm(p.start)}-{hhmm(p.end)}, {p.orders.count} parts"
            + (" (latest)" if p.id == latest else "")
            for p in recipe.productions
        )
        stations = "\n".join(
            f"  {sid} ({s.type_name}): {(type(s).__doc__ or '').strip().splitlines()[0]}"
            for sid, s in factory.stations.items()
        )
        return (
            f"Route of every part: {' -> '.join(recipe.route)}\n"
            f"Part dimension: {recipe.part.nominal_mm:.3f} mm +/- {recipe.part.tolerance_mm:.3f} mm\n"
            f"Stations:\n{stations}\nProductions (military time):\n{productions}"
        )
    if topic in factory.stations:
        return glossary_text([topic])
    meanings = [
        f"{sid}: {topic}: {s.events[topic]}"
        for sid, s in factory.stations.items() if topic in s.events
    ]
    if meanings:
        return "\n".join(meanings)
    raise ToolError(f"Unknown topic {topic!r}. Use 'cell', a station id ({', '.join(factory.stations)}) "
                    "or an event name.")


def _filter(
    production: str | None,
    station: str | None,
    event: str | None,
    part: str | None,
    contains: str | None,
    start: str | None,
    end: str | None,
) -> list[LogLine]:
    check_production(production)
    check_station(station)
    lines = factory.logbook.lines(
        station, production,
        parse_hhmm(start) if start else None,
        parse_hhmm(end) if end else None,
    )
    words = _whole_words(contains) if contains else None
    return [
        line for line in lines
        if (event is None or line.event == event)
        and (part is None or line.part == part)
        and (words is None or words.search(line.text()))
    ]


def _whole_words(text: str) -> re.Pattern:
    """'LOAD' matches 'LOAD' and 'result=LOAD', not 'UNLOAD' nor 'load_pct'."""
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(text.strip())}(?![A-Za-z0-9_])", re.IGNORECASE)


def _why_empty(production: str | None, station: str | None, event: str | None,
               part: str | None) -> str:
    """Explain an empty search, so the model does not read it as missing data."""
    reasons = []
    if event is not None:
        loggers = sorted({line.station for line in factory.logbook.lines() if line.event == event})
        if not loggers:
            reasons.append(f"No station logs an event called {event}; see describe for event names.")
        elif station is not None and station not in loggers:
            reasons.append(f"{event} is logged by {', '.join(loggers)}, not by {station}.")
    if part is not None:
        homes = sorted({line.production for line in factory.logbook.lines() if line.part == part})
        if not homes:
            reasons.append(f"No line mentions part {part}.")
        elif production is not None and production not in homes:
            reasons.append(f"Part {part} belongs to {', '.join(homes)}, not to {production}.")
    return " ".join(reasons) or (
        "No line matched these filters. This does not mean the event did not happen: "
        "loosen a filter or check names with describe. contains matches whole words only."
    )


class QueryResult(BaseModel):
    matched: int
    shown: int
    truncated: bool
    hint: str | None
    lines: str


def query(
    production: str | None = None,
    station: str | None = None,
    event: str | None = None,
    part: str | None = None,
    contains: str | None = None,
    start: MilitaryTime | None = None,
    end: MilitaryTime | None = None,
    limit: int = 50,
) -> QueryResult:
    """Search the logs. Every filter is optional; combine them.

    Examples: part='P-0404' is the whole history of a part; event='GAUGE' with
    contains='REJECT' lists rejects; station='M1' with start/end is a time window;
    start/end without station shows what the whole cell did around a moment.
    Lines of other productions are prefixed with their production id.

    Args:
        production: Production id, e.g. 'PO-1001'. Omit to search every production.
        station: Station id, e.g. 'WH1'.
        event: Exact event name, e.g. 'GAUGE'.
        part: Part id, e.g. 'P-0301'.
        contains: Whole word(s) that must appear in the line, case-insensitive,
            e.g. 'REJECT' (it does not match 'REJECTED').
        start: From this minute, military time, e.g. '0900'.
        end: Before this minute, military time, e.g. '1000'.
        limit: Maximum lines to return (at most 150).
    """
    lines = _filter(production, station, event, part, contains, start, end)
    shown = lines[:max(1, min(limit, MAX_LINES))]
    prefix = production is None
    hint = None
    if not lines:
        hint = _why_empty(production, station, event, part)
    elif len(shown) < len(lines):
        hint = (f"Only the first {len(shown)} of {len(lines)} lines are shown, the earliest ones. "
                "Narrow the search with event=, part= or a start/end window.")
    return QueryResult(
        matched=len(lines),
        shown=len(shown),
        truncated=len(shown) < len(lines),
        hint=hint,
        lines="\n".join((f"{line.production} " if prefix else "") + line.text() for line in shown),
    )


class CountResult(BaseModel):
    group_by: str
    matched: int
    counts: dict[str, int]


def count(
    group_by: str,
    production: str | None = None,
    station: str | None = None,
    event: str | None = None,
    part: str | None = None,
    contains: str | None = None,
    start: MilitaryTime | None = None,
    end: MilitaryTime | None = None,
) -> CountResult:
    """Count log lines grouped by a field, without reading them. Same filters as query.

    group_by can be 'production', 'station', 'event', 'part', or any field that
    appears in the lines, like 'result', 'tool' or 'reason'.
    Example: group_by='result', event='GAUGE' counts OK and REJECT gauges.

    Args:
        group_by: Field to group by.
        production: Production id. Omit to count every production.
        station: Station id.
        event: Exact event name.
        part: Part id.
        contains: Whole word(s) that must appear in the line, case-insensitive.
        start: From this minute, military time.
        end: Before this minute, military time.
    """
    lines = _filter(production, station, event, part, contains, start, end)

    def key(line: LogLine) -> str:
        if group_by in ("production", "station", "event", "part"):
            return str(getattr(line, group_by) or "(none)")
        return str(line.fields.get(group_by, "(none)"))

    counts = Counter(key(line) for line in lines)
    return CountResult(group_by=group_by, matched=len(lines), counts=dict(counts.most_common(30)))


class QuoteCheck(BaseModel):
    found: list[str]
    missing: list[str]


def quote_exists(raw: str) -> bool:
    """A quote matches a log line with the same time, station and event whose
    fields include every field quoted (fields may be left out, not changed)."""
    quote = " ".join(raw.strip().strip("*`-> ").split())
    quote = re.sub(r"^PO-\S+ ", "", quote)
    tokens = quote.split()
    if len(tokens) < 3:
        return False
    for line in factory.logbook.lines():
        text = line.text().split()
        if text[:3] == tokens[:3] and set(tokens[3:]) <= set(text[3:]):
            return True
    return False


def check_quotes(lines: list[str]) -> QuoteCheck:
    """Check that log lines you want to quote really exist in the logs. Call it before
    answering, and do not quote lines reported as missing.

    Args:
        lines: The log lines you plan to quote, e.g. ['0958 M1 LOAD part=P-0404'].
    """
    found, missing = [], []
    for raw in lines:
        (found if quote_exists(raw) else missing).append(raw)
    return QuoteCheck(found=found, missing=missing)


# A quoted log line inside an answer: "HHMM STATION EVENT ...".
QUOTE = re.compile(r"(?<![0-9])(?:[01][0-9]|2[0-3])[0-5][0-9] [A-Z][A-Z0-9]* [A-Z][A-Z_]+[^\n`*]*")


def verify_answer(answer: str) -> str | None:
    """Host-side check of a final answer: every quoted log line must exist.

    Returns None to accept the answer, or the message the host sends back.
    """
    quotes = [q.strip() for q in QUOTE.findall(answer)]
    if not quotes:
        return ("Host check: your answer quotes no log lines. Quote the lines that "
                "prove it, exactly as the tools returned them.")
    missing = [q for q in quotes if not quote_exists(q)]
    if missing:
        listed = "\n".join(f"- {q}" for q in missing)
        return ("Host check: these lines you quoted do not exist in the logs:\n"
                f"{listed}\nOnly quote lines the tools returned. Investigate further "
                "if needed, then answer again.")
    return None


# --- grading (host side, never shown to the model) ---------------------------------

SECTIONS = ["summary", "symptom", "root cause", "evidence", "ruled out", "open questions"]
PART = re.compile(r"P-(\d{4})(?:\s*(?:-|–|—|to)\s*P-(\d{4}))?")


def _sections(answer: str) -> dict[str, str]:
    """Split a markdown report into its sections, keyed by lowercase title."""
    parts = re.split(r"^#{1,4}\s*(.+?)\s*$", answer, flags=re.MULTILINE)
    return {title.strip().lower(): body for title, body in zip(parts[1::2], parts[2::2])}


def _parts(text: str) -> set[str]:
    """Part ids in a text; 'P-0404-P-0408' counts as five parts."""
    found = set()
    for first, last in PART.findall(text):
        end = int(last) if last else int(first)
        found |= {f"P-{n:04d}" for n in range(int(first), end + 1)}
    return found


def _mentions(text: str, words: Sequence[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}", text, re.IGNORECASE) for w in words)


def grade_report(answer: str) -> list[tuple[str, str, str]]:
    """Score a report against the simulator's truth: (aspect, verdict, note) rows."""
    truth = factory.truth()
    sections = _sections(answer)
    section = lambda name: sections.get(name, answer if not sections else "")
    rows = []

    missing = [name for name in SECTIONS if name not in sections]
    rows.append(("Format", "✓" if not missing else "~" if sections else "✗",
                 "all sections" if not missing else f"missing: {', '.join(missing)}"))

    rejected = set(truth.rejected)
    named = _parts(section("symptom"))
    first_ok = truth.first_rejected in named
    rows.append((
        "Symptom",
        "✓" if first_ok and rejected <= named else "~" if first_ok or named & rejected else "✗",
        f"{len(named & rejected)}/{len(rejected)} rejected parts, first {truth.first_rejected} "
        + ("named" if first_ok else "missing")
        + (f", {len(named - rejected)} extra" if named - rejected else ""),
    ))

    cause = truth.causes[0]
    keywords = factory.stations[cause.station].faults[cause.fault].keywords
    text = section("root cause")
    station_ok = re.search(rf"\b{cause.station}\b", text) is not None
    exact, partial = _mentions(text, keywords["exact"]), _mentions(text, keywords["partial"])
    rows.append((
        "Root cause",
        "✓" if station_ok and exact else "~" if station_ok or exact or partial else "✗",
        f"truth: {cause.station} {cause.fault}; station "
        + ("named" if station_ok else "missing")
        + ("; mechanism named" if exact else "; only related words" if partial else "; mechanism missing"),
    ))

    quotes = [q.strip() for q in QUOTE.findall(section("evidence"))]
    real = [q for q in quotes if quote_exists(q)]
    proving = [q for q in real if _mentions(q, keywords["exact"])
               or ("REJECT" in q and _parts(q) & rejected)]
    rows.append((
        "Evidence",
        "✗" if not real else "✓" if len(real) == len(quotes) and proving else "~",
        f"{len(quotes)} log line(s) quoted, {len(quotes) - len(real)} invented, "
        f"{len(proving)} prove the cause or the rejects",
    ))

    production = next(p.production for p in factory.parts if p.id == truth.first_rejected)
    others = [
        f for f in factory.recipe.faults
        if f.production == production and (f.station, f.kind) != (cause.station, cause.fault)
    ]
    text = section("ruled out")
    ruled = [f for f in others if re.search(rf"\b{f.station}\b", text)
             or _mentions(text, factory.stations[f.station].faults[f.kind].keywords["exact"])]
    rows.append((
        "Ruled out",
        "✓" if len(ruled) == len(others) else "~" if ruled else "✗",
        f"{len(ruled)}/{len(others)} other events of {production} discussed"
        + (f" ({', '.join(f'{f.station} {f.kind}' for f in others)})" if others else ""),
    ))

    text = section("summary")
    rows.append((
        "Summary",
        "✓" if _mentions(text, keywords["exact"]) else "~" if _mentions(text, keywords["partial"])
        or re.search(rf"\b{cause.station}\b", text) else "✗",
        "consistent with the real cause" if _mentions(text, keywords["exact"]) else "does not name the mechanism",
    ))
    return rows


# --- resource and prompt -------------------------------------------------------------


def glossary() -> str:
    """What every event of every station means."""
    return glossary_text()


def investigate_rejects(production: str) -> str:
    """A root-cause procedure for parts rejected by the final gauge."""
    return (
        f"Parts of production {production} were rejected by the final gauge when they "
        "came back to the warehouse. Find the root cause, following these steps:\n"
        "1. Find which parts the final gauge rejected in this production, and the first one.\n"
        "2. Follow one rejected part upstream, station by station.\n"
        "3. Compare it with a part of the same production that passed the gauge. "
        "What is different?\n"
        "4. Look at what the suspect station logged just before the first rejected part.\n"
        "5. Rule out other events of the same period, and say why.\n"
        "Answer with: the station, the cause, the first rejected part, and the log lines "
        "that prove it. Only quote lines you have actually read."
    )


# --- registry ----------------------------------------------------------------------

TOOLS: dict[str, Callable] = {
    fn.__name__: fn
    for fn in [
        describe_cell, get_log, read_log_page,
        production_summary, part_history,
        describe, query, count, check_quotes,
    ]
}
RESOURCES: dict[str, Callable] = {"cell://glossary": glossary}
PROMPTS: dict[str, Callable] = {"investigate_rejects": investigate_rejects}


def register(
    mcp: MCPServer,
    tools: Sequence[str] = (),
    resources: Sequence[str] = (),
    prompts: Sequence[str] = (),
) -> None:
    """Register the chosen capabilities on the MCP server."""
    for name in tools:
        mcp.tool()(TOOLS[name])
    for uri in resources:
        mcp.resource(uri, description=RESOURCES[uri].__doc__, mime_type="text/plain")(RESOURCES[uri])
    for name in prompts:
        mcp.prompt()(PROMPTS[name])
