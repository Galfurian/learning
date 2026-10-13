"""Causal rules: an explanation is a rule over the chain, not a guess of the generator.

A rule names its pattern, its version, and the events that match it. The
generator may only repeat an explanation that a rule produced; with no rule
matching, the answer says what happened and that the recording does not say why.
"""

from dataclasses import dataclass

from .chain import Chain

CAUSES_VERSION = "1"
REWORK_MISSIONS = ("take_cover_top_from_pallet", "take_cover_bottom_from_pallet", "drop_covers_in_bin")


@dataclass(frozen=True)
class Explanation:
    rule: str
    version: str
    cause: list[str]        # event ids of the cause
    effect: list[str]       # event ids of the effect
    text: str
    claim_kind: str         # "derived" if every link is observed or derived, else "inferred"


def rework_after_failed_check(c: Chain) -> Explanation | None:
    """A failed QC check, then the covers taken off the pallet and dropped in the bin: a rework."""
    failed = [e for e in c.steps if e.activity == "check_failed"]
    if not failed:
        return None
    after = [e for e in c.steps if e.activity == "mission_started" and e.attrs.get("mission") in REWORK_MISSIONS
             and e.event_time > failed[0].event_time]
    if not {"take_cover_top_from_pallet", "drop_covers_in_bin"} <= {e.attrs["mission"] for e in after}:
        return None
    kind = "inferred" if any(e.claim_kind == "inferred" for e in [failed[0], *after]) else "derived"
    who = sorted({e.resource for e in after})
    return Explanation("rework-after-failed-check", CAUSES_VERSION, [failed[0].event_id], [e.event_id for e in after],
                       f"the QC check failed, then {', '.join(who)} took the covers off pallet {c.pallet} "
                       f"and dropped them in the bin: a rework", kind)


RULES = (rework_after_failed_check,)


def explain(c: Chain) -> list[Explanation]:
    return [x for rule in RULES if (x := rule(c)) is not None]


def explanation_lines(c: Chain) -> list[str]:
    out = []
    for x in explain(c):
        ids = ", ".join(x.cause + x.effect)
        link = "inferred link to the pallet" if x.claim_kind == "inferred" else "derived"
        out.append(f"[{ids}] cause (rule {x.rule} v{x.version}): {x.text} ({link})")
    if not out:
        out.append("(cause) no causal rule matches this case: the recording shows what happened, not why")
    return out
