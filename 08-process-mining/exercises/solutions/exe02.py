"""EXE02 — event abstraction. Reference solution (the same rules as pmlab.abstraction.Case.place)."""

from pmlab.abstraction import Case, Unit, same_record
from pmlab.runners import run_abstract


def match_operations(case: Case, units: list[Unit]) -> None:
    for unit in units:
        if unit.activity == "bay_stay":
            continue                                   # the stays come later (rule 2, in pmlab)
        found = case.candidates(unit)                  # (operation, step index), most specific steps
        if not found:
            case.unmapped.append(unit)
            continue
        names = {name for name, _ in found}
        # reload_covers and load_covers have the same missions: the fail-branch operation
        # wins once everything it depends on (bin_covers) has started; before, it cannot run.
        fail = {n for n in names if case.ops[n].branch == "fail"}
        ready = {n for n in fail if all(case.started(d, unit.begin) for d in case.ops[n].depends)}
        names = ready or (names - fail) or names
        steps = {n: [i for c, i in found if c == n] for n in names}

        # Join the most recent instance of a matching operation, if it can take the unit.
        latest = {n: case.latest(n) for n in names}
        placed = False
        for name in sorted((n for n in names if latest[n]), key=lambda n: -case.instances.index(latest[n])):
            inst = latest[name]
            if any(same_record(unit, u) for u in list(inst.units.values()) + inst.extra):
                inst.extra.append(unit)                # a duplicated record
            elif free := [i for i in steps[name] if i not in inst.units]:
                inst.units[free[0]] = unit             # a step the instance still lacks
            elif case.consecutive(inst, unit):
                inst.extra.append(unit)                # one more part of the same cell operation
            else:
                continue
            placed = True
            break
        if not placed:                                 # a new instance of the operation
            name = case.in_context(names)
            case.new(name).units[steps[name][0]] = unit


if __name__ == "__main__":
    run_abstract(match_operations, __file__)
