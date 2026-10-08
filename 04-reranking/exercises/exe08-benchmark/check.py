from reranklab.checks import run_checks
from reranklab.corpus import HOLDOUT_QUESTIONS
from reranklab.evalset import load_questions


def checks(exe, check):
    holdout = load_questions(HOLDOUT_QUESTIONS)
    check.ok(len(holdout) == 20, "the holdout has 20 questions", len(holdout))
    check.ok(sum(not q.answerable for q in holdout) == 3, "3 of them have no answer")
    check.ok(callable(exe.run_benchmark), "exe08 runs the shared benchmark")


run_checks(checks, __file__.replace("check.py", "exe08.py"))
