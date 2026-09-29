"""EXE04 — chaining tools. Task: see README.md in this folder."""

from pydantic import BaseModel

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe04-campus")

PROMPT = "In which rooms are the courses of the student Giulia Neri held?"

STUDENTS = {
    "giulia neri": "VR-48213",
    "marco bianchi": "VR-50977",
}

ENROLLMENTS = {
    "VR-48213": ["EMB-01", "NET-07"],
    "VR-50977": ["NET-07", "ML-03"],
}

COURSES = {
    "EMB-01": {"title": "Embedded Systems", "room": "Aula Delta"},
    "NET-07": {"title": "Computer Networks", "room": "Aula Gamma"},
    "ML-03": {"title": "Machine Learning", "room": "Aula Alfa"},
}


class Course(BaseModel):
    code: str
    title: str
    room: str


# TODO: register this function as an MCP tool, add a docstring, implement it.
def find_student(full_name: str) -> str:
    raise NotImplementedError


# TODO: register this function as an MCP tool, add a docstring, implement it.
def student_courses(student_id: str) -> list[Course]:
    raise NotImplementedError


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
