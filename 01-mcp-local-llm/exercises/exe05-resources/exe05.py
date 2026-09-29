"""EXE05 — resources: context chosen by the host. Task: see README.md in this folder."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe05-lab-rules")

PROMPT = "Can I use the laser cutter alone on Saturday evening?"

RULES = """\
Laboratory rules (Building C, ground floor)

1. The lab is open Monday to Friday, 08:00-19:00.
2. On Saturday the lab is open 09:00-13:00 only, with a technician present.
3. Nobody may work alone in the lab outside opening hours.
4. The laser cutter requires a second trained person in the room at all times.
5. Soldering stations must be switched off before leaving.
"""

MACHINES = {
    "laser-cutter": "Laser cutter: trained users only, never unattended, ventilation on.",
    "3d-printer": "3D printer: may run unattended during opening hours.",
}


# TODO: register this function as the MCP resource `lab://rules`, implement it.
def lab_rules() -> str:
    raise NotImplementedError


# TODO: register this function as the MCP resource template
# `lab://machines/{machine}`, implement it.
def machine_notes(machine: str) -> str:
    raise NotImplementedError


if __name__ == "__main__":
    # The HOST decides which resources to read and put in the model's context.
    run(mcp, PROMPT, __file__, attach=["lab://rules", "lab://machines/laser-cutter"])
