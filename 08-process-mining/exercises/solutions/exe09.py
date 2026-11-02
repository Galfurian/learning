"""EXE09 — online monitoring. Reference solution (the same result as pmlab.monitor.candidates)."""

from pmlab.log import Trace
from pmlab.monitor import Candidates, continuations, known_labels, prefix_fit
from pmlab.petri import Net
from pmlab.runners import run_candidates


def candidates(prefix: Trace, nets: dict[str, Net]) -> Candidates:
    known = known_labels(nets)

    def fitting(entries) -> dict:
        seen = Trace(prefix.case_id, list(entries))
        return {n: f for n in sorted(nets) if (f := prefix_fit(nets[n], seen, known)) is not None}

    fits = fitting(prefix.entries)
    if not fits:
        return Candidates([], {}, "derived")
    if len(fits) == 1:
        # The deciding entry: the latest one after which the count of candidates became one.
        ids, before = (), len(fitting([]))
        for i, e in enumerate(prefix.entries):
            if e.activity not in known:
                continue
            now = len(fitting(prefix.entries[:i + 1]))
            if now == 1 and before != 1:
                ids = e.source_ids
            before = now
        return Candidates(list(fits), {}, "derived", ids)

    # Deciding activities: per candidate, the nearest activities ahead that not every candidate has.
    rest = {n: continuations(nets[n], f) for n, f in fits.items()}
    seen = {n: {a for seq in seqs for a in seq} for n, seqs in rest.items()}
    common = set.intersection(*seen.values())
    deciding: dict[str, list[str]] = {}
    for seqs in rest.values():
        dist: dict[str, int] = {}
        for seq in seqs:
            for i, a in enumerate(seq):
                if a not in common and i < dist.get(a, len(seq) + 1):
                    dist[a] = i
        low = min(dist.values(), default=None)
        deciding |= {a: sorted(n for n in fits if a in seen[n]) for a, d in dist.items() if d == low}
    return Candidates(list(fits), dict(sorted(deciding.items())), "inferred")


if __name__ == "__main__":
    run_candidates(candidates, __file__)
