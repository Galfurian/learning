"""Question -> plan: the start nodes, a relation path, list or count.

The plan is a small DSL, plain JSON:

    {"start": ["bay 5"], "path": ["^serves_bay"], "op": "list"}

`start` holds mentions (resolved later, like extracted mentions); `path`
holds relations, '^' to walk an edge backwards; `op` is "list" or "count".

Two planners write it:

- RulePlanner: patterns written by hand. Fast, predictable, and blind to any
  phrasing its author did not foresee;
- LLMPlanner: a generative model fills the same JSON (schema in `format`).
  It reads any phrasing, and it can pick a wrong hop.

A wrong hop is a wrong answer, so the path is scored apart (metrics.path_correct).
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .client import DEFAULT_CHAT_MODEL, Tracer, chat
from .extract import LINK_RELATIONS
from .scorecache import ScoreCache

TREE_RELATIONS = ("contains", "exposes_variable", "exposes_method", "has_parameter", "returns", "has_alarm")
ALL_RELATIONS = (*TREE_RELATIONS, *LINK_RELATIONS)


@dataclass(frozen=True)
class Plan:
    start: tuple[str, ...]
    path: tuple[str, ...]
    op: str = "list"
    why: str = ""            # which rule fired, or "llm"

    def to_json(self) -> dict[str, Any]:
        return {"start": list(self.start), "path": list(self.path), "op": self.op}


def valid(plan: Plan) -> bool:
    return bool(plan.start) and plan.op in ("list", "count") and all(
        r.lstrip("^") in ALL_RELATIONS for r in plan.path)


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: str             # a regex on the question, lowercase; named group "x" is the start mention
    path: tuple[str, ...]
    op: str = "list"


@dataclass
class RulePlanner:
    rules: list[Rule] = field(default_factory=list)

    def plan(self, question: str) -> Plan | None:
        text = question.lower().strip()
        for rule in self.rules:
            m = re.search(rule.pattern, text)
            if m:
                return Plan((m.group("x").strip(" ?.,"),), rule.path, rule.op, rule.name)
        return None


PLAN_PROMPT = """You turn a question about a production line into a graph query.
The graph has these relations (subject -> object):
{relations}
Return JSON: "start" is a list of entity names copied from the question; "path" is the list of
relations to follow from them, in order; write "^relation" to follow a relation from object to
subject; "op" is "count" if the question asks how many, else "list"."""

TREE_TEXT = """- contains: line, cell, device or folder -> what is inside it
- exposes_variable: device or folder -> variable
- exposes_method: device or folder -> method
- has_parameter: method -> parameter
- returns: method -> returned variable
- has_alarm: device -> alarm"""


def plan_schema() -> dict[str, Any]:
    relation = {"type": "string", "enum": [*ALL_RELATIONS, *(f"^{r}" for r in ALL_RELATIONS)]}
    return {
        "type": "object",
        "properties": {
            "start": {"type": "array", "items": {"type": "string"}},
            "path": {"type": "array", "items": relation},
            "op": {"type": "string", "enum": ["list", "count"]},
        },
        "required": ["start", "path", "op"],
    }


def plan_messages(question: str) -> list[dict[str, str]]:
    links = "\n".join(f"- {name}: {s} -> {o}: {meaning}" for name, (s, o, meaning) in LINK_RELATIONS.items())
    return [
        {"role": "system", "content": PLAN_PROMPT.format(relations=TREE_TEXT + "\n" + links)},
        {"role": "user", "content": question},
    ]


def parse_plan(raw: str) -> Plan | None:
    try:
        data = json.loads(raw)
        plan = Plan(tuple(data["start"]), tuple(data["path"]), data.get("op", "list"), "llm")
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return plan if valid(plan) else None


@dataclass
class LLMPlanner:
    model: str = DEFAULT_CHAT_MODEL
    cache: ScoreCache | None = None
    tracer: Tracer | None = None

    def plan(self, question: str) -> Plan | None:
        msgs = plan_messages(question)
        parts = ["plan", self.model, *(m["content"] for m in msgs)]
        raw = self.cache.get(parts) if self.cache else None
        if raw is None:
            raw = chat(self.model, msgs, format=plan_schema(), tracer=self.tracer).content
            if self.cache:
                self.cache.put(parts, raw)
        return parse_plan(raw)


# Written by reading the dev questions, as a developer would. The holdout
# shows what they miss.
DEFAULT_RULES = [
    Rule("count-serve-bay", r"how many devices serve (?P<x>bay \d+)", ("^serves_bay",), "count"),
    Rule("count-stop", r"how many alarms stop (?P<x>.+?)\?", ("^stops",), "count"),
    Rule("who-serves-bay", r"which devices serve (?P<x>bay \d+)", ("^serves_bay",)),
    Rule("bays-of", r"which bays does (?P<x>.+?) serve", ("serves_bay",)),
    Rule("share-bay", r"from (?P<x>.+?), which devices share", ("serves_bay", "^serves_bay")),
    Rule("same-item", r"handle the kind of item carried by (?P<x>.+?)\?", ("moves", "^moves")),
    Rule("items-of", r"(?:which items can|what can) (?P<x>.+?) (?:move|carry)", ("moves",)),
    Rule("who-moves", r"which devices move (?:a |an |the )?(?P<x>.+?)\?", ("^moves",)),
    Rule("four-hops", r"four route hops from (?P<x>bay \d+)", ("next_step",) * 4),
    Rule("two-hops", r"follows (?P<x>bay \d+) after two", ("next_step", "next_step")),
    Rule("next-bay", r"follows (?P<x>bay \d+)", ("next_step",)),
    Rule("alarm-stops", r"which alarm stops (?P<x>.+?)\?", ("^stops",)),
    Rule("stopped-by", r"stopped by (?:the )?(?P<x>.+?)\?", ("stops",)),
    Rule("incident-device-vars", r"exposed by the device involved in the (?P<x>.+?)\?",
         ("incident_on", "contains", "exposes_variable")),
    Rule("incident-alarm-device", r"alarm raised in the (?P<x>.+?)\?", ("raised", "^has_alarm")),
    Rule("incident-device", r"which device was named by the (?P<x>.+?)\?", ("incident_on",)),
    Rule("incident-alarm", r"which alarm did .+? report on (?P<x>\d+ \w+)", ("raised",)),
    Rule("confirmed-by-status", r"mission is confirmed by (?:the |a variable in )?(?P<x>.+?)'s", ("contains", "exposes_variable", "confirms")),
    Rule("observe-conditions", r"observe the (?P<x>.+?) method conditions", ("contains", "exposes_method", "requires", "observed_by")),
    Rule("conditions-vars", r"conditions required by (?P<x>.+?) methods", ("exposes_method", "requires", "observed_by")),
    Rule("tells-may-run", r"tells .+? whether (?P<x>\w+) may run", ("requires", "observed_by")),
    Rule("requires", r"which condition does (?P<x>\w+) require", ("requires",)),
    Rule("owner-alarm", r"which device owns the (?P<x>.+?)\?", ("^has_alarm",)),
    Rule("returns", r"what .+? does the (?P<x>.+?) return", ("returns",)),
    Rule("parameters", r"which input names does (?P<x>\w+) accept", ("has_parameter",)),
    Rule("folder-of", r"which folder exposes the (?P<x>.+?)\?", ("^exposes_variable",)),
    Rule("cell-devices", r"which devices belong to the (?P<x>.+?)\?", ("contains",)),
]
