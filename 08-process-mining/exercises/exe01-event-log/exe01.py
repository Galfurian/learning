"""EXE01 — the event log and the case notion. Task: see README.md in this folder."""

from pmlab.log import Entry, Trace
from pmlab.runners import run_to_log


# TODO: group the entries into traces, one trace per case.
# - case_notion "order": the case is entry.case_id.
# - case_notion "pallet": the case is each "pallet:<n>" in entry.objects. An
#   entry with two pallets goes into both traces (a copy); an entry with no
#   pallet goes into no trace (it is lost).
# - Any other case_notion: raise ValueError.
# - Inside a trace, sort the entries by (time, number of the first source id):
#   "e9" comes before "e10" (pmlab.log.sort_key does this).
# - Sort the traces by case id: shorter id first, then the text
#   ("order:9" before "order:10").
def to_log(entries: list[Entry], case_notion: str = "order") -> list[Trace]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_to_log(to_log, __file__)
