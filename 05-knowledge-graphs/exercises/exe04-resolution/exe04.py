"""EXE04 — entity resolution: a mention -> one node, or none, or "ambiguous". Task: see README.md in this folder."""

from kglab.metrics import AMBIGUOUS
from kglab.runners import run_resolve


# TODO 1: normalize a name so that small differences disappear.
# - split CamelCase words ("NoAirPressure" -> "No Air Pressure");
# - lowercase; every character that is not a letter, a digit, ":", "/", " " or "-" becomes a space;
# - runs of spaces and "-" become one space; strip; drop a leading "the ".
# "The  First-Rover!" -> "first rover"; "NoAirPressure" -> "no air pressure".
def normalize(text: str) -> str:
    raise NotImplementedError("You need to implement this function.")


# TODO 2: resolve one mention.
# exact:  name or id as written -> set of node ids; normal: normalize(name or alias) -> set of node ids.
# - exactly one exact hit: (that node, "exact");
# - else look up normalize(mention) (or keep several exact hits): one node -> (node, "normalized");
# - several nodes -> (AMBIGUOUS, "ambiguous"): never pick one, that would merge two entities;
# - nothing -> (None, "none").
def resolve(mention: str, exact: dict[str, set[str]], normal: dict[str, set[str]]) -> tuple[str | None, str]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_resolve(normalize, resolve, __file__)
