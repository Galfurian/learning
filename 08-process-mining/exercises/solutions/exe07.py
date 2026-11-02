"""EXE07 — alignments. Reference solution."""

from pmlab.align import Alignment
from pmlab.align import align as _align
from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.runners import run_align


def align(net: Net, trace: Trace, *, complete: bool = True) -> Alignment:
    return _align(net, trace, complete=complete)


if __name__ == "__main__":
    run_align(align, __file__)
