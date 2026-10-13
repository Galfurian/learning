"""Extraction: one chunk of prose -> (subject, relation, object) triples, with a fixed schema.

The model writes mentions as they appear in the text ("the first rover"),
not node ids; resolution (resolve.py) maps them to nodes later. Keeping the
two steps apart shows which one fails.

The relation list is part of the JSON schema sent in Ollama's `format`
field, so the model cannot invent a relation name. It can still pick the
wrong one, or keep a fact the text denies: the schema constrains the form,
not the truth.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .client import DEFAULT_CHAT_MODEL, Tracer, chat
from .scorecache import ScoreCache

# relation -> (subject type, object type, meaning)
LINK_RELATIONS: dict[str, tuple[str, str, str]] = {
    "serves_bay": ("Device", "Bay", "the device loads or unloads pallets at that conveyor bay"),
    "next_step": ("Bay", "Bay", "on the route, pallets go from the first bay to the second"),
    "moves": ("Device", "Item or Pallet", "the device carries or handles that item or pallet"),
    "stops": ("Alarm", "Device", "when the alarm is active, the device stops"),
    "confirms": ("Variable", "Mission or Method", "the variable reports the result of that mission or method"),
    "requires": ("Method", "Condition", "the method runs only when the condition is true"),
    "observed_by": ("Condition", "Variable", "the variable tells whether the condition is true"),
    "incident_on": ("Incident", "Device", "the incident happened on that device"),
    "raised": ("Incident", "Alarm", "the incident raised that alarm"),
    "fixed_by_method": ("Incident", "Method", "calling that method fixed the incident"),
}

SYSTEM_PROMPT = """You extract facts from the notes of a production line.
Return only facts that the text states. Do not infer. Do not return a fact that the text denies.
Use only these relations (subject -> object):
{relations}
Write subject and object as they appear in the text, short (a name, not a sentence).
If the text states no such fact, return an empty list."""


def relations_text() -> str:
    return "\n".join(f"- {name}: {s} -> {o}: {meaning}" for name, (s, o, meaning) in LINK_RELATIONS.items())


def json_schema(*, constrained: bool = True) -> dict[str, Any]:
    """The output form. constrained=False lets any string be a relation, to count invalid ones."""
    relation: dict[str, Any] = {"type": "string"}
    if constrained:
        relation["enum"] = list(LINK_RELATIONS)
    return {
        "type": "object",
        "properties": {
            "triples": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": relation,
                        "object": {"type": "string"},
                    },
                    "required": ["subject", "relation", "object"],
                },
            }
        },
        "required": ["triples"],
    }


def messages(title: str, text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(relations=relations_text())},
        {"role": "user", "content": f"Section: {title}\n\n{text}"},
    ]


@dataclass(frozen=True)
class Mention:
    subject: str
    relation: str
    object: str


@dataclass
class Extraction:
    triples: list[Mention]
    invalid: list[dict[str, Any]] = field(default_factory=list)  # not parseable, or out of schema
    seconds: float = 0.0
    raw: str = ""


def parse_triples(raw: str) -> tuple[list[Mention], list[dict[str, Any]]]:
    """The model's JSON text -> valid mentions, and the items that are not valid."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return [], [{"error": "no JSON object", "raw": raw[:200]}]
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return [], [{"error": "no JSON object", "raw": raw[:200]}]
    items = data.get("triples", []) if isinstance(data, dict) else []
    valid, invalid = [], []
    for item in items:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip()
                                                 for k in ("subject", "relation", "object")):
            invalid.append({"error": "missing field", "item": item})
        elif item["relation"] not in LINK_RELATIONS:
            invalid.append({"error": "relation not in schema", "item": item})
        else:
            valid.append(Mention(item["subject"].strip(), item["relation"], item["object"].strip()))
    return valid, invalid


def extract(title: str, text: str, *, model: str = DEFAULT_CHAT_MODEL, constrained: bool = True,
            cache: ScoreCache | None = None, tracer: Tracer | None = None) -> Extraction:
    """One request per chunk. The cache key covers the model, the schema mode, the prompt and the chunk,
    so a changed prompt re-extracts and nothing stale is reused. `seconds` is the time of the first run."""
    msgs = messages(title, text)
    parts = ["extract", model, str(constrained), *(m["content"] for m in msgs)]
    stored = cache.get(parts) if cache else None
    if stored is None:
        result = chat(model, msgs, format=json_schema(constrained=constrained), tracer=tracer)
        stored = {"raw": result.content, "seconds": result.seconds}
        if cache:
            cache.put(parts, stored)
    triples, invalid = parse_triples(stored["raw"])
    return Extraction(triples, invalid, stored["seconds"], stored["raw"])
