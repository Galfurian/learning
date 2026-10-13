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
from .scenario import SCENARIO
from .scorecache import ScoreCache

ALL_RELATIONS = tuple(SCENARIO.relations)


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
        text = question.strip()
        for rule in self.rules:
            m = re.search(rule.pattern, text.lower())
            if m:  # the mention keeps the question's case: "MovePallet", not "movepallet"
                return Plan((text[m.start("x"):m.end("x")].strip(" ?.,"),), rule.path, rule.op, rule.name)
        return None


PLAN_PROMPT = """You turn a question about {domain} into a graph query.
The graph has these relations (subject -> object):
{relations}
Return JSON: "start" is a list of entity names copied from the question; "path" is the list of
relations to follow from them, in order; write "^relation" to follow a relation from object to
subject; "op" is "count" if the question asks how many, else "list"."""

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
    relations = "\n".join(f"- {r.name}: {' or '.join(r.subject)} -> {' or '.join(r.object)}: {r.meaning}"
                          for r in SCENARIO.relations.values())
    return [
        {"role": "system", "content": PLAN_PROMPT.format(domain=SCENARIO.generation["domain"], relations=relations)},
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
            raw = chat(self.model, msgs, format=plan_schema(), max_tokens=256, tracer=self.tracer).content
            if self.cache:
                self.cache.put(parts, raw)
        return parse_plan(raw)


# The scenario's rules, written by reading its dev questions, as a developer would.
# The holdout shows what they miss.
DEFAULT_RULES = [Rule(r["name"], r["pattern"], tuple(r["path"]), r.get("op", "list")) for r in SCENARIO.planner_rules]
