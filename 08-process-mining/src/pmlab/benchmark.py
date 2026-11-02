"""The benchmark: each question through the whole pipeline, scored stage by stage.

    log -> abstract -> to_log -> SELECT the order and the time -> MINE (recipe,
    open operation, alignment) -> evidence lines -> ANSWER

First failing stage:

    SELECTION   the question did not lead to the gold order or the gold time
    MINING      the candidates, the open operations or the moves differ from
                the gold, or a gold id is not in the evidence lines
    GENERATION  the evidence was right, the answer was not (wrong ids, refusal,
                no "probably" on an inferred line, a missing expected term, ...).
                An abstention is the refusal, or an answer that matches every
                "all" group of the question (no free pass for vague words).
    NONE        right
"""

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .answer import Answer, answer, line_ids, mentions_inference
from .evidence import Finding, Mined, log_path, mine, pipeline  # noqa: F401  (log_path for the tests)
from .recipes import UNIT_ROOT

DEV = UNIT_ROOT / "data" / "dev.json"
HOLDOUT = UNIT_ROOT / "data" / "holdout.json"
STAGES = ("SELECTION", "MINING", "GENERATION", "NONE")
TYPES = ("which-recipe", "where", "stopped", "conformance", "normal", "abstain")
LOG_NAMES = ("train", "holdout", "ref-order", "ref-stuck", "ref-skip-check", "ref-no-end", "ref-prefix")
ORDER = re.compile(r"\border[\s:#]*(\d+)\b", re.I)
TIME = re.compile(r"\bt\s*=\s*(\d+(?:\.\d+)?)\s*s\b|\bat (\d+(?:\.\d+)?)\s*s\b", re.I)

Generator = Callable[[dict[str, Any], list[str]], Answer]


def load_questions(path: Path) -> list[dict[str, Any]]:
    """Questions name their log by a logical name (`train`, `holdout`, `ref-*`)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["questions"]


def select(question: str, m: Mined, now: float) -> tuple[str | None, float]:
    """The order and the time a question is about. `now` is the clock when it is
    asked; a time in the text ("at t=900 s") wins. With no order in the text, the
    only order of the log, else none."""
    o = ORDER.search(question)
    order = f"order:{o.group(1)}" if o else (next(iter(m.traces)) if len(m.traces) == 1 else None)
    t = TIME.search(question)
    return order, float(t.group(1) or t.group(2)) if t else now


@dataclass
class Row:
    id: str
    type: str
    stage: str
    evidence_recall: float
    cited_gold: float
    unknown_ids: int
    refused: bool
    answer: str = ""
    notes: list[str] = field(default_factory=list)


def expectation(q: dict[str, Any], text: str) -> list[str]:
    """Every group of "all" has a term in the text, no group of "none" has one (a group is synonyms)."""
    exp = q.get("expect") or {}
    low = text.lower()

    def found(group) -> bool:
        return any(t.lower() in low for t in group) if isinstance(group, list) else group.lower() in low

    return ([f"missing {g!r}" for g in exp.get("all", []) if not found(g)]
            + [f"says {g!r}" for g in exp.get("none", []) if found(g)])


def _gold_recipes(q: dict[str, Any]) -> list[str]:
    g = q.get("gold_recipe", [])
    return sorted([g] if isinstance(g, str) else g)


def mining_errors(q: dict[str, Any], f: Finding) -> list[str]:
    notes = []
    if sorted(f.recipes) != _gold_recipes(q):
        notes.append(f"recipes {sorted(f.recipes)}, gold {_gold_recipes(q)}")
    found_open = [[o.activity, o.verdict] for o in f.open]
    if found_open != [list(o) for o in q.get("gold_open", [])]:
        notes.append(f"open {found_open}, gold {q.get('gold_open', [])}")
    found_moves = [list(mv) for mv in f.moves]
    if found_moves != [list(mv) for mv in q.get("gold_moves", [])]:
        notes.append(f"moves {found_moves}, gold {q.get('gold_moves', [])}")
    return notes


def _cites_line_of(gold_id: str, lines: Sequence[str], cited: Sequence[str]) -> bool:
    """A gold event counts as cited when the answer cites it, or any id of an evidence line
    that holds it: a line is one statement, and its ids are cited together."""
    if gold_id in cited:
        return True
    return any(gold_id in ids and ids & set(cited) for ids in (line_ids([line]) for line in lines))


COPY_MIN = 40      # characters: a shorter line is a fact, a longer one copied whole is a dump


def copied_lines(text: str, lines: Sequence[str]) -> int:
    """How many evidence lines the answer copies word for word (ids and claim kind left out).
    The prompt says "do not copy the lines": a copy has the facts but does not answer."""
    body = " ".join(text.split()).lower()
    count = 0
    for line in lines:
        core = re.sub(r"^\[[^\]]*\]\s*", "", line)
        core = re.sub(r"\s*\((derived|inferred|observed|confirmed|coverage)\)\s*$", "", core)
        core = " ".join(core.split()).lower()
        if len(core) >= COPY_MIN and core in body:
            count += 1
    return count


def score(q: dict[str, Any], order: str | None, now: float, f: Finding, a: Answer) -> Row:
    gold = q.get("gold_ids", [])
    have = line_ids(f.lines)
    recall = sum(g in have for g in gold) / len(gold) if gold else 1.0
    cited = sum(_cites_line_of(g, f.lines, a.cited) for g in gold) / len(gold) if gold else 1.0
    row = Row(q["id"], q["type"], "NONE", recall, cited, len(a.unknown), a.refused, a.text)
    if order != q["order"] or now != q["now"]:
        row.stage = "SELECTION"
        row.notes.append(f"chose {order} at t={now:g} s, gold {q['order']} at t={q['now']:g} s")
        return row
    wrong = mining_errors(q, f)
    if recall < 1.0:
        wrong.append(f"gold ids in the evidence: {recall:.0%}")
    if wrong:
        row.stage = "MINING"
        row.notes += wrong
        return row
    missing = expectation(q, a.text)
    if q["abstain"]:
        # an abstention is the refusal, or an explicit answer that matches every "all" group of the question
        explicit = bool((q.get("expect") or {}).get("all")) and not missing
        ok = (a.refused or explicit) and not a.unknown
        if a.refused:
            missing = [m for m in missing if m.startswith("says")]
    else:
        ok = not a.refused and not a.unknown and (cited > 0 or not gold)
        if a.refused:
            row.notes.append("refused, although the lines answer")
        elif gold and cited == 0:
            row.notes.append("cites no line that holds a gold event")
        inferred = any(line.endswith("(inferred)") and line_ids([line]) & set(gold) for line in f.lines)
        if ok and inferred and not mentions_inference(a.text):
            ok = False
            row.notes.append("an inferred line is told as observed")
    if missing:
        ok = False
        row.notes += missing
    if a.unknown:
        row.notes.append(f"cites ids not in the evidence: {a.unknown}")
    copies = copied_lines(a.text, f.lines) if not a.refused else 0
    if copies:
        ok = False
        row.notes.append(f"copies {copies} evidence line(s) instead of answering")
    if not ok:
        row.stage = "GENERATION"
    return row


def run(questions: Sequence[dict[str, Any]], *, model: str | None = None, progress=None,
        generator: Generator | None = None, system: str | None = None) -> list[Row]:
    """Each question: select, mine, answer, score. `generator` replaces the model (tests use a stub);
    `system` replaces the system prompt (EXE12)."""
    if generator is None:
        def generator(q, lines):
            return answer(q["text"], lines, **({"model": model} if model else {}),
                          **({"system": system} if system else {}))
    rows = []
    for q in questions:
        m = pipeline(q["log"])
        order, now = select(q["text"], m, q["now"])
        f = mine(m, order, now) if order else Finding("", now, [], [], [], ["the question names no order (derived)"])
        rows.append(score(q, order, now, f, generator(q, f.lines)))
        if progress:
            progress(rows[-1])
    return rows


def summary(rows: Sequence[Row]) -> dict[str, Any]:
    n = len(rows) or 1
    return {
        "questions": len(rows),
        "right": sum(r.stage == "NONE" for r in rows),
        "stages": {s: sum(r.stage == s for r in rows) for s in STAGES},
        "evidence_recall": sum(r.evidence_recall for r in rows) / n,
        "gold_cited": sum(r.cited_gold for r in rows) / n,
        "answers_with_unknown_ids": sum(r.unknown_ids > 0 for r in rows),
    }
