"""EXE03 — extraction: the model's JSON -> valid mentions. Task: see README.md in this folder."""

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
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_extract(parse_triples, __file__)
