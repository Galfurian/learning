"""EXE02 — when did it happen: event time from the playback position. Reference solution."""

import bisect

from evlab.runners import run_place


def place(wall: float, polls: list[tuple[float, float]]) -> tuple[float, float, float]:
    walls = [w for w, _ in polls]
    i = bisect.bisect_right(walls, wall)
    if i == 0 or i == len(polls):
        p = polls[0][1] if i == 0 else polls[-1][1]
        return p, p, p
    (w0, p0), (w1, p1) = polls[i - 1], polls[i]
    return p0 + (p1 - p0) * (wall - w0) / (w1 - w0), p0, p1


if __name__ == "__main__":
    run_place(place, __file__)
