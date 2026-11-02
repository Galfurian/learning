"""EXE12 — improve the generator. Task: see README.md in this folder."""

from pmlab.runners import run_prompt_experiment

# TODO: change ONE thing in this prompt, run it on dev (3 runs), compare with
# the unit's prompt (--baseline), and keep a note of what you changed and what
# happened. Then the next change. The holdout runs once, at the very end.
# It starts as a copy of the unit's prompt (pmlab.answer.SYSTEM_PROMPT).
SYSTEM_PROMPT = """You answer questions about orders on a production line.
Use only the evidence lines in the user message. A line starts with event ids in square brackets.
After every sentence, write the ids of the lines it uses, for example [e12].
A line marked inferred is not observed: say probably.
A "why" can come only from a line that gives a cause; if no line gives one, say the recording does not show why.
Unusual is a comparison with the baseline on the line, not a cause.
Write two to four sentences in your own words. Do not copy the lines. Cite only ids that appear in the lines.
If the lines do not answer the question, reply exactly: Not in the recording."""

if __name__ == "__main__":
    run_prompt_experiment(SYSTEM_PROMPT, __file__)
