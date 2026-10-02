"""Turn a series of readings into a short neutral sentence. Ordinary code.

    describe("dim_mm", Signal(39.95, 40.05, 3), [40.001, 40.002, 40.121, 40.124], ["0850", ...])
    -> "dim_mm: step up at 0852, above nominal (40.001 -> 40.124, nominal 39.950-40.050)"

It says what the signal does (stable, rising, falling, step up/down) and where
it ends compared with its nominal range. It never says why.
"""

from statistics import mean

from line import Signal

STEP_SIGMAS = 4
TREND_SIGMAS = 3


def shape(values: list[float], times: list[str], noise: float) -> str:
    if len(values) < 4:
        return "too few readings"
    # A step: the best split into two flat halves with very different means.
    best, at = 0.0, 2
    for k in range(2, len(values) - 1):
        jump = mean(values[k:]) - mean(values[:k])
        if abs(jump) > abs(best):
            best, at = jump, k
    flat = max(max(values[:at]) - min(values[:at]), max(values[at:]) - min(values[at:]))
    if abs(best) > STEP_SIGMAS * noise and flat < abs(best) / 2:
        return f"step {'up' if best > 0 else 'down'} at {times[at]}"
    change = mean(values[-3:]) - mean(values[:3])
    if abs(change) > TREND_SIGMAS * noise:
        return "rising" if change > 0 else "falling"
    return "stable"


def status(value: float, signal: Signal) -> str:
    if value > signal.high:
        return "above nominal"
    if value < signal.low:
        return "below nominal"
    return "within nominal"


def describe(name: str, signal: Signal, values: list[float], times: list[str]) -> str:
    # A whole-number signal cannot move by less than 1: that is its noise floor.
    noise = max(signal.noise, 10 ** -signal.decimals)
    form = shape(values, times, noise)
    where = status(mean(values[-3:]), signal)
    digits = signal.decimals
    if form == "stable":
        span = f"{min(values):.{digits}f}-{max(values):.{digits}f}"
    else:
        span = f"{values[0]:.{digits}f} -> {values[-1]:.{digits}f}"
    return f"{name}: {form}, {where} ({span}, nominal {signal.nominal()})"
