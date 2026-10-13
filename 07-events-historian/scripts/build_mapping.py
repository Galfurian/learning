"""Build .local/mapping.json from .local/patterns.json and the simulator's catalog (needs ICE_SIM_URL).

    uv run python scripts/build_mapping.py --trace lab-session
"""

import argparse
import json

from evlab.build_mapping import PATTERNS, resolve, write_local
from evlab.recordings import real_trace
from evlab.sim import Sim


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trace", default="lab-session", help="A logical alias (.local/traces.json).")
    args = p.parse_args()
    patterns = json.loads(PATTERNS.read_text(encoding="utf-8"))
    sim = Sim()
    servers = {spec["server"] for spec in patterns["machines"].values()}
    catalog = {s: sim.nodes(s, trace=real_trace(args.trace), with_data=False) for s in servers}
    path = write_local(resolve(patterns, catalog))
    print(f"wrote {path} ({sum(len(v['signals']) for v in patterns['machines'].values())} signals)")


if __name__ == "__main__":
    main()
