"""pm4py adapters. The only module of src that imports pm4py (tests and checks use it).

The check scripts import pm4py from here (`from pmlab.reference import pm4py`):
no welcome banner and no progress bars in their output.
"""

import os

os.environ.setdefault("PM4PY_SHOW_PROGRESS_BAR", "False")

import pandas as pd  # noqa: E402
import pm4py  # noqa: E402
from pm4py.objects.petri_net.obj import Marking, PetriNet  # noqa: E402
from pm4py.objects.petri_net.utils import petri_utils  # noqa: E402

from pmlab.log import Trace  # noqa: E402
from pmlab.petri import Net  # noqa: E402


def to_pm4py_log(traces: list[Trace]):
    """Complete entries of each trace as a pm4py event log."""
    rows = [
        {"case:concept:name": t.case_id, "concept:name": e.activity, "time:timestamp": pd.Timestamp(e.time, unit="s")}
        for t in traces
        for e in t.entries
        if e.lifecycle == "complete"
    ]
    return pm4py.format_dataframe(pd.DataFrame(rows), case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")


def to_pm4py(net: Net) -> tuple[PetriNet, Marking, Marking]:
    """Convert a Net to a pm4py net with its initial and final markings."""
    pn = PetriNet("net")
    places = {p: PetriNet.Place(p) for p in sorted(net.places)}
    trans = {t: PetriNet.Transition(t, label) for t, label in sorted(net.transitions.items())}
    for p in places.values():
        pn.places.add(p)
    for t in trans.values():
        pn.transitions.add(t)
    for a, b in sorted(net.arcs):
        if a in places:
            petri_utils.add_arc_from_to(places[a], trans[b], pn)
        else:
            petri_utils.add_arc_from_to(trans[a], places[b], pn)
    im = Marking({places[p]: n for p, n in net.initial.items()})
    fm = Marking({places[p]: n for p, n in net.final.items()})
    return pn, im, fm
