"""EXE04 — solution."""

from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

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


@mcp.tool()
def find_student(full_name: str) -> str:
    """Look up the student ID (matricola) of a student by name.

    The student ID is required by student_courses.

    Args:
        full_name: First and last name, for example 'Marco Bianchi'.
    """
    key = " ".join(full_name.lower().split())
    if key not in STUDENTS:
        raise ToolError(f"Unknown student: {full_name}")
    return STUDENTS[key]


@mcp.tool()
def student_courses(student_id: str) -> list[Course]:
    """List the courses a student is enrolled in, with title and room.

    Args:
        student_id: Student ID exactly as returned by find_student.
    """
    if student_id not in ENROLLMENTS:
        raise ToolError(f"Unknown student ID: {student_id!r}. Call find_student first.")
    return [Course(code=code, **COURSES[code]) for code in ENROLLMENTS[student_id]]


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
