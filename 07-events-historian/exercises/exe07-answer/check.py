from evlab.answer import REFUSAL
from evlab.chain import Chain
from evlab.checks import run_checks
from evlab.records import Event


def ev(i, t, activity, resource, kind="observed", **attrs):
    return Event(f"e{i}", activity, resource, t, t, t, (f"c{i}",), "r", "1", kind, 7, "p7#1", attrs)


CHAIN = Chain("p7#1", 7, [ev(1, 10, "check_failed", "qc_station", "inferred")], [], 0, ["links are inferred"])


def checks(exe, check):
    done, out = check.calls(exe.messages, "Why?", CHAIN)
    if not done:
        return
    check.ok([m["role"] for m in out] == ["system", "user"], "a system message, then one user message")
    system, user = out[0]["content"], out[1]["content"]
    for need, what in (("[e", "an example citation"), ("inferred", "inferred links"), ("cause", "causes only from cause lines"),
                       (REFUSAL, "the exact refusal")):
        check.ok(need in system, f"the system prompt covers {what}", system[:200])
    check.ok("Evidence:" in user and "[e1]" in user and user.rstrip().endswith("Question: Why?"),
             "the user message: evidence lines with ids, then the question", user[-200:])
    empty = exe.messages("Why?", None)[1]["content"]
    check.ok("(no evidence)" in empty, "no chain: '(no evidence)'", empty)


run_checks(checks, __file__.replace("check.py", "exe07.py"))
