"""EXE02 — when did it happen: event time from the playback position. Task: see README.md in this folder."""

from evlab.runners import run_place


# TODO: place one notification in trace time.
# wall: the collector's clock when the notification arrived.
# polls: (wall, position) pairs, sorted by wall: the playback position read every 0.5 s.
# Return (event_time, lo, hi):
# - lo and hi are the positions of the poll before and the poll after the notification;
# - event_time is the linear interpolation between them;
# - before the first poll: all three are the first position; after the last poll: the last position.
# Do not use the server's SourceTimestamp: on the simulator it is the time the value was written.
def place(wall: float, polls: list[tuple[float, float]]) -> tuple[float, float, float]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_place(place, __file__)
