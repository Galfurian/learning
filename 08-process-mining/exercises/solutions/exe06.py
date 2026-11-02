"""EXE06 — token replay. Reference solution."""

from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.replay import Replay
from pmlab.replay import token_replay as _token_replay
from pmlab.runners import run_replay


def token_replay(net: Net, trace: Trace, *, complete: bool = True) -> Replay:
    return _token_replay(net, trace, complete=complete)


if __name__ == "__main__":
    run_replay(token_replay, __file__)
