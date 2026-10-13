"""Metrics, one family per stage, because each stage fails in its own way.

- extraction: precision, recall and F1 of triples, per relation;
- resolution: mentions resolved to the right node, exact against normalized;
- query: the planned path against the gold path, apart from the answer set;
- answer: the returned set against the gold set, or the count.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

Triple = tuple[str, str, str]


@dataclass(frozen=True)
class PRF:
    tp: int
    predicted: int
    gold: int

    @property
    def precision(self) -> float:
        return self.tp / self.predicted if self.predicted else 0.0

    @property
    def recall(self) -> float:
        return self.tp / self.gold if self.gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def prf(predicted: Iterable, gold: Iterable) -> PRF:
    predicted, gold = set(predicted), set(gold)
    return PRF(len(predicted & gold), len(predicted), len(gold))


def triple_scores(predicted: Iterable[Triple], gold: Iterable[Triple]) -> dict[str, PRF]:
    """Per relation, plus 'all'. A triple is right only if subject, relation and object all match."""
    predicted, gold = set(predicted), set(gold)
    by_rel: dict[str, tuple[set, set]] = defaultdict(lambda: (set(), set()))
    for t in predicted:
        by_rel[t[1]][0].add(t)
    for t in gold:
        by_rel[t[1]][1].add(t)
    scores = {rel: prf(p, g) for rel, (p, g) in sorted(by_rel.items())}
    scores["all"] = prf(predicted, gold)
    return scores


def path_correct(planned: Sequence[str] | None, gold: Sequence[str] | None) -> bool:
    """The same relations in the same order. A right answer can hide a wrong path."""
    if planned is None or gold is None:
        return planned is None and gold is None
    return tuple(planned) == tuple(gold)


def answer_scores(returned: Iterable[str], gold: Iterable[str]) -> PRF:
    return prf(returned, gold)


@dataclass(frozen=True)
class ResolutionCounts:
    right: int = 0
    wrong: int = 0        # resolved to another node (a merge error when two mentions meet there)
    unresolved: int = 0   # no node (a split error: the mention stays apart)
    ambiguous_ok: int = 0  # said "ambiguous" where the gold says ambiguous
    ambiguous_missed: int = 0  # picked one node where the gold says ambiguous

    @property
    def total(self) -> int:
        return self.right + self.wrong + self.unresolved + self.ambiguous_ok + self.ambiguous_missed

    @property
    def accuracy(self) -> float:
        return (self.right + self.ambiguous_ok) / self.total if self.total else 0.0


AMBIGUOUS = "<ambiguous>"


def resolution_counts(pairs: Iterable[tuple[str | None, str]]) -> ResolutionCounts:
    """pairs: (resolved node id, or None, or AMBIGUOUS; gold node id or AMBIGUOUS)."""
    c = dict(right=0, wrong=0, unresolved=0, ambiguous_ok=0, ambiguous_missed=0)
    for got, gold in pairs:
        if gold == AMBIGUOUS:
            c["ambiguous_ok" if got == AMBIGUOUS else "ambiguous_missed"] += 1
        elif got == gold:
            c["right"] += 1
        elif got is None or got == AMBIGUOUS:
            c["unresolved"] += 1
        else:
            c["wrong"] += 1
    return ResolutionCounts(**c)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
