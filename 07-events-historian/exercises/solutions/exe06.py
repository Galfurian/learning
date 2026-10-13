"""EXE06 — evidence chain. Reference solution."""

from evlab.chain import chain as _chain
from evlab.chain import Chain
from evlab.records import Event
from evlab.runners import run_chain


def chain(events: list[Event], case_id: str) -> Chain:
    return _chain(events, case_id)


if __name__ == "__main__":
    run_chain(chain, __file__)
