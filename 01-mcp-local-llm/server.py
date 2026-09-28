from mcp.server import MCPServer

mcp = MCPServer("learning-lab")

INVENTORY = {
    "flux-capacitor": 3,
    "servo-x12": 17,
    "lidar-mini": 5,
}

PROJECT_CODES = {
    "atlas": "A7-KAPPA",
    "orion": "O4-DELTA",
}


@mcp.tool()
def inventory_count(part: str) -> int:
    """Return the number of units currently in the lab inventory.

    Args:
        part: Part name, for example 'flux-capacitor' or 'servo-x12'.
    """
    key = part.strip().lower()
    if key not in INVENTORY:
        raise ValueError(f"Unknown part: {part}")
    return INVENTORY[key]


@mcp.tool()
def project_code(project: str) -> str:
    """Return the internal demo code associated with a project.

    Args:
        project: Project name, for example 'atlas' or 'orion'.
    """
    key = project.strip().lower()
    if key not in PROJECT_CODES:
        raise ValueError(f"Unknown project: {project}")
    return PROJECT_CODES[key]


if __name__ == "__main__":
    mcp.run(transport="stdio")
