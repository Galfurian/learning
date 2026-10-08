from reranklab.checks import run_checks


def checks(exe, check):
    done, a = check.calls(exe.state_a, "What is X?", "X is a lens.")
    if not done:
        return
    check.ok("What is X?" in a and "X is a lens." in a and a.index("What is X?") < a.index("X is a lens."),
             "mode A state: the question, then the one passage", a)
    q = exe.QUESTION_A.get("relevant") if isinstance(exe.QUESTION_A, dict) else None
    check.ok(isinstance(q, dict) and q.get("type") == "noul" and q.get("instructions", "").endswith("?"),
             "QUESTION_A has a noul question named 'relevant'", exe.QUESTION_A)
    done, b = check.calls(exe.state_b, "What is X?", ["one", "two", "three"])
    if not done:
        return
    check.ok(all(f"Passage {i}:\n{t}" in b for i, t in enumerate(["one", "two", "three"], start=1)),
             "mode B state: every passage, numbered from 1", b)
    done, qs = check.calls(exe.questions_b, 3)
    if not done:
        return
    check.ok(list(qs) == ["p1", "p2", "p3"], "one question per passage, named p1..pN", list(qs))
    check.ok(all(v.get("type") == "noul" and str(i) in v.get("instructions", "") for i, v in enumerate(qs.values(), start=1)),
             "each question is noul and names its passage number")


run_checks(checks, __file__.replace("check.py", "exe04.py"))
