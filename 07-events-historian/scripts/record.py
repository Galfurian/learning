"""Record one ice-sim trace through OPC-UA into .cache/recordings/ (needs ICE_SIM_URL and .local/mapping.json).

    uv run python scripts/record.py --trace lab-session --speed 1      # benchmark recording (about 19 min)
    uv run python scripts/record.py --trace lab-session --speed 10     # smoke test (about 2 min)

One worker, decommissioned at the end, also on errors and Ctrl-C.
"""

import argparse
import asyncio

from evlab.collector import manifest_for, record, to_changes
from evlab.mapping import LOCAL_MAPPING, load_mapping
from evlab.records import write_recording
from evlab.recordings import real_trace, recording_path
from evlab.sim import Sim


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trace", required=True, help="A logical alias from .local/traces.json.")
    p.add_argument("--speed", type=float, default=1.0)
    args = p.parse_args()
    if not LOCAL_MAPPING.exists():
        raise SystemExit("no .local/mapping.json: run scripts/build_mapping.py first")
    mapping, _ = load_mapping(LOCAL_MAPPING)
    with Sim().worker(real_trace(args.trace), speed=args.speed) as worker:
        manifest = manifest_for(worker, mapping, args.speed)
        last = [-60.0]

        def progress(position: float, count: int) -> None:
            if position - last[0] >= 60:
                last[0] = position
                print(f"  position {position:7.1f} s · {count} notifications", flush=True)

        notes, polls = asyncio.run(record(worker, mapping, progress=progress))
    changes = to_changes(notes, polls, mapping, manifest.trace_id, manifest.trace_version)
    path = recording_path(args.trace, manifest)
    write_recording(path, manifest, changes)
    print(f"{len(changes)} changes -> {path}")


if __name__ == "__main__":
    main()
