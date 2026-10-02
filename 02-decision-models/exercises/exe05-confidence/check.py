import math

from declab.checks import fake_choice, run_checks

# Real answers returned by Ollama, with the confidence it computed.
RECORDED = [
    (
        {
            "duplicate_charge": 0.7233431949612822,
            "cancel_subscription": 0.2620814988952114,
            "card_declined": 0.0005499391255430105,
            "none": 0.014025367017963329,
        },
        0.531704180564901,
    ),
    ({"summer": 0.08246196803691683, "winter": 0.39955348393569273, "unknown": 0.5179845480273905}, 0.16889164307425042),
    ({"0": 0.13446519307107396, "1": 0.5297872028791577, "2": 0.3357476040497683}, 0.11452450255688285),
]


def checks(exe, check):
    for probabilities, expected in RECORDED:
        done, value = check.calls(exe.confidence, probabilities)
        if not done:
            break
        check.ok(
            isinstance(value, float) and math.isclose(value, expected, abs_tol=1e-6),
            f"confidence() matches Ollama's value {expected:.4f}",
            value,
        )
    else:
        check.ok(math.isclose(exe.confidence({"a": 0.5, "b": 0.5}), 0.0, abs_tol=1e-9), "uniform -> 0", exe.confidence({"a": 0.5, "b": 0.5}))
        check.ok(math.isclose(exe.confidence({"a": 1.0, "b": 0.0}), 1.0), "all mass on one option -> 1", exe.confidence({"a": 1.0, "b": 0.0}))

    done, value = check.calls(exe.margin, {"a": 0.6, "b": 0.3, "c": 0.1})
    if done:
        check.ok(math.isclose(value, 0.3), "margin({a: 0.6, b: 0.3, c: 0.1}) == 0.3", value)

    for probabilities, starts, note in [
        ({"normal": 0.95, "spam": 0.03, "insult": 0.02}, "publish", "normal 0.95 -> publish"),
        ({"normal": 0.85, "spam": 0.10, "insult": 0.05}, "publish", "normal 0.85 -> publish (threshold 0.8)"),
        ({"normal": 0.02, "spam": 0.97, "insult": 0.01}, "delete", "spam 0.97 -> delete"),
        ({"normal": 0.05, "spam": 0.10, "insult": 0.85}, "send to a human moderator", "insult 0.85 -> a human decides (threshold 0.9)"),
        ({"normal": 0.40, "spam": 0.20, "insult": 0.40}, "send to a human moderator", "a tie -> a human decides"),
    ]:
        done, action = check.calls(exe.act, "any post", {"kind": fake_choice(probabilities)})
        if not done:
            return
        check.ok(isinstance(action, str) and action.startswith(starts), note, action)


run_checks(checks, __file__.replace("check.py", "exe05.py"))
