"""EXE05 — the recipe as a Petri net. Task: see README.md in this folder."""

from pmlab.petri import Net
from pmlab.recipes import Recipe
from pmlab.runners import run_compile


# TODO: compile a recipe into a workflow net (one "source" place, one "sink").
# - One transition per operation: id = label = the operation name.
# - Main operations (branch "main"): one place "A>B" per dependency (B depends
#   on A). Several successors: an AND split; several dependencies: an AND join.
# - Main operations with no dependency take from "source"; main operations
#   with no main successor put into "sink". When there are several, add a
#   silent transition "start" (or "end", label None) to split (or join).
# - The fail branch: a main operation M followed by fail operations puts its
#   token into the place "M?". A silent "M:pass" moves it on to M's main
#   successors; the first fail operation takes it instead, the fail chain
#   runs, and the last fail operation puts back a token in every input place
#   of M, so M runs again.
# - initial = Counter({"source": 1}), final = Counter({"sink": 1}).
def compile_recipe(recipe: Recipe) -> Net:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_compile(compile_recipe, __file__)
