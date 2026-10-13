"""The benchmark: each question through the whole pipeline, scored stage by stage.

    recording -> clean -> derive -> cases -> SELECT the evidence -> chain -> causes -> ANSWER

First failing stage:

    SELECTION   the question did not lead to the gold case (or to the gold events)
    EVIDENCE    the chosen chain lacks a gold event
    GENERATION  the evidence was right, the answer was not (wrong ids, refusal, missing "inferred", ...)
    NONE        right
"""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .answer import Answer, answer, mentions_inference
from .cases import assign_cases
from .chain import Chain, chain
from .mapping import UNIT_ROOT
from .records import Event, read_recording
from .recordings import resolve
from .rules import clean, derive

DEV = UNIT_ROOT / "data" / "dev.json"
HOLDOUT = UNIT_ROOT / "data" / "holdout.json"
STAGES = ("SELECTION", "EVIDENCE", "GENERATION", "NONE")
NO_WHY = re.compile(r"not (show|say|explain|in the recording)|does not (show|say|explain)|no (cause|rule|reason)|"
                    r"cannot (tell|say|conclude)|unknown", re.I)


def load_questions(path: Path) -> list[dict[str, Any]]:
    """Questions name their recording by a logical alias ("lab-session", "holdout", "fixture")."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [{**q, "recording": q.get("recording") or data.get("recording")} for q in data["questions"]]


def recording_for(alias: str) -> Path:
    return resolve(alias)


def pipeline(path: Path) -> list[Event]:
    _, changes = read_recording(path)
    kept, _ = clean(changes)
    return assign_cases(derive(kept))


PALLET = re.compile(r"\bpallet (\d+)\b", re.I)


def select(question: str, events: Sequence[Event]) -> Chain:
    """The evidence a question is about: a pallet's case, or else the events of the resources and codes it names."""
    m = PALLET.search(question)
    if m:
        pallet = int(m.group(1))
        cases = sorted({e.case_id for e in events if e.pallet == pallet and e.case_id},
                       key=lambda c: int(c.split("#")[1]))
        if cases:
            return chain(events, cases[0])
        loose = [e for e in events if e.pallet == pallet and e.activity not in ("pallet_entered_segment",
                                                                                 "pallet_left_segment")]
        return Chain(f"p{pallet}#?", pallet, loose, [], 0,
                     ["no product case of this pallet: these events belong to no cycle"] if loose
                     else ["no event of this pallet in the recording"])
    words = {w.lower() for w in re.findall(r"[A-Za-z_]+\d*", question)}
    steps = [e for e in events if e.activity not in ("pallet_entered_segment", "pallet_left_segment")
             and (e.resource.lower() in words or any(str(v).lower() in words for v in e.attrs.values()))]
    return Chain("resource", None, steps, [], 0, [] if steps else ["no event of the named resources"])


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
    """The question's machine-checkable expectations: every term of "all" appears, no term of "none" does."""
    exp = q.get("expect") or {}
    low = text.lower()

    def found(term) -> bool:   # a list is a group of synonyms: any one is enough
        return any(t.lower() in low for t in term) if isinstance(term, list) else term.lower() in low

    missing = [t for t in exp.get("all", []) if not found(t)]
    present = [t for t in exp.get("none", []) if found(t)]
    return [f"missing {t!r}" for t in missing] + [f"says {t!r}" for t in present]


def score(q: dict[str, Any], c: Chain, a: Answer) -> Row:
    gold = q.get("gold_event_ids", [])
    have = set(c.ids)
    recall = sum(g in have for g in gold) / len(gold) if gold else 1.0
    cited = sum(g in a.cited for g in gold) / len(gold) if gold else 1.0
    row = Row(q["id"], q["type"], "NONE", recall, cited, len(a.unknown), a.refused, a.text)
    if q.get("gold_case") and c.case_id != q["gold_case"]:
        row.stage = "SELECTION"
        row.notes.append(f"chose {c.case_id}, gold {q['gold_case']}")
        return row
    if recall < 1.0:   # also for abstentions: they must abstain on the right evidence
        row.stage = "SELECTION" if recall == 0 else "EVIDENCE"
        row.notes.append(f"gold events in the evidence: {recall:.0%}")
        return row
    if q["abstain"]:
        ok = (a.refused or bool(NO_WHY.search(a.text))) and not a.unknown
    elif q["type"] == "why-no-rule":
        ok = bool(NO_WHY.search(a.text)) or a.refused
    else:
        ok = not a.refused and not a.unknown and cited > 0
        if ok and any(e.claim_kind == "inferred" for e in c.steps if e.event_id in gold):
            ok = mentions_inference(a.text)
            if not ok:
                row.notes.append("an inferred link is told as observed")
    wrong = expectation(q, a.text)
    if wrong:
        ok = False
        row.notes += wrong
    if a.unknown:
        row.notes.append(f"cites ids not in the evidence: {a.unknown}")
    if not ok:
        row.stage = "GENERATION"
    return row


def run(questions: Sequence[dict[str, Any]], *, model: str | None = None, progress=None) -> list[Row]:
    events_by_key: dict[str, list[Event]] = {}
    rows = []
    for q in questions:
        key = q["recording"]
        if key not in events_by_key:
            events_by_key[key] = pipeline(recording_for(key))
        c = select(q["text"], events_by_key[key])
        a = answer(q["text"], c, **({"model": model} if model else {}))
        rows.append(score(q, c, a))
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
