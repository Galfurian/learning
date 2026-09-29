"""EXE06 — resources loaded on demand. Task: see README.md in this folder."""

from mcp.server import MCPServer
from mcp.server.mcpserver.resources import TextResource

from mcplab.exercise import run

mcp = MCPServer("exe06-manuals")

PROMPT = "What is the maximum thickness of acrylic I can cut with the laser cutter?"

MANUALS = {
    "laser-cutter": {
        "summary": "Laser cutter manual: allowed materials, maximum thickness, power and speed settings.",
        "text": """\
Laser cutter LC-60 — operating manual

Allowed materials: acrylic, plywood, MDF, cardboard, leather.
Forbidden materials: PVC, polycarbonate, anything containing chlorine.

Maximum thickness per material:
- acrylic: 8 mm
- plywood: 6 mm
- MDF: 5 mm
- cardboard: 4 mm

Settings: start at 60% power and 15 mm/s for acrylic, then adjust.
Always turn on the ventilation before cutting. Never leave the machine
unattended while the laser is firing.
""",
    },
    "3d-printer": {
        "summary": "3D printer manual: supported filaments, nozzle temperatures, bed levelling.",
        "text": """\
3D printer P-220 — operating manual

Supported filaments: PLA, PETG, TPU. ABS is not allowed (no enclosure).

Nozzle temperatures:
- PLA: 205 °C
- PETG: 235 °C
- TPU: 220 °C

Bed: level it before every print with the paper test at all four corners.
Heated bed at 60 °C for PLA, 80 °C for PETG.
""",
    },
    "oscilloscope": {
        "summary": "Oscilloscope manual: bandwidth, probe compensation, trigger setup.",
        "text": """\
Oscilloscope DS-1104 — operating manual

Bandwidth: 100 MHz, 4 channels, 1 GSa/s shared sample rate.

Probes: compensate each 10x probe on the 1 kHz calibration output before
use. Adjust the trimmer until the square wave has flat tops.

Trigger: start with edge trigger on the measured channel, 50% level.
""",
    },
    "reflow-oven": {
        "summary": "Reflow oven manual: solder paste profiles and peak temperatures.",
        "text": """\
Reflow oven RO-3 — operating manual

Profiles:
- leaded paste (Sn63Pb37): peak 215 °C for 30 s
- lead-free paste (SAC305): peak 245 °C for 30 s

Never open the door during the peak phase. Let boards cool below 60 °C
before touching them.
""",
    },
}

# TODO: register every manual as a static MCP resource with URI
# lab://manuals/<machine>. Use its summary as the description.
for machine, manual in MANUALS.items():
    ...


if __name__ == "__main__":
    # The host lists the manuals up front but reads one only when needed.
    run(mcp, PROMPT, __file__, on_demand_resources=True)
