"""Recipes: what the line produces and what goes wrong. Times are military."""

from line import FaultAt, Recipe

DEFAULT = Recipe(
    parts=80,
    faults=[
        FaultAt("0820", "C1", "jam"),            # slows the line down
        FaultAt("0850", "M1", "wrong_offset"),   # bad parts, seen downstream at Q1
        FaultAt("0910", "Q1", "gauge_drift"),    # looks like bad parts, but the parts are fine
    ],
)

QUIET = Recipe(parts=30)  # nothing breaks: the supervisor should stay silent
