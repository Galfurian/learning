"""EXE05 — the recipe as a Petri net. Reference solution."""

from pmlab.compile import compile_recipe as _compile_recipe
from pmlab.petri import Net
from pmlab.recipes import Recipe
from pmlab.runners import run_compile


def compile_recipe(recipe: Recipe) -> Net:
    return _compile_recipe(recipe)


if __name__ == "__main__":
    run_compile(compile_recipe, __file__)
