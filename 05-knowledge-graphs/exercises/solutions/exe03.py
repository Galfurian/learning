"""EXE03 — extraction: the model's JSON -> valid mentions. Reference solution."""

from typing import Any

from kglab.extract import LINK_RELATIONS, Mention
from kglab.runners import run_extract


# TODO: turn the model's raw text into (valid mentions, invalid items).
# - raw should be a JSON object {"triples": [{"subject": ..., "relation": ..., "object": ...}, ...]};
#   if json.loads fails, try the first {...} block in the text; if that fails too, return
#   ([], [{"error": "no JSON object", "raw": raw[:200]}]);
# - an item is valid when subject, relation and object are non-empty strings and the relation is
#   in LINK_RELATIONS; keep it as Mention(subject.strip(), relation, object.strip());
# - otherwise add {"error": "missing field", "item": item} or
#   {"error": "relation not in schema", "item": item} to the invalid list.
# Never repair a relation name: an invalid item is a measurement, not a typo to fix.
def parse_triples(raw: str) -> tuple[list[Mention], list[dict[str, Any]]]:
    import json
    import re

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        try:
            data = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            data = None
        if data is None:
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


if __name__ == "__main__":
    run_extract(parse_triples, __file__)
