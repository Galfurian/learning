from ..fault import Fault
from ..machine import Machine
from ..part import NOMINAL_MM, TOLERANCE_MM
from ..signal import Signal

REFERENCE_MM = 25.000
MIN_IMAGE_SCORE = 0.80


class DirtyLens(Fault):
    description = "The camera lens is dirty: image quality drops and good parts are rejected."
    remedy = "clean the camera lens"

    def affect(self, machine, readings, part):
        readings["image_score"] = round(machine.rng.gauss(0.70, 0.04), 2)


class GaugeDrift(Fault):
    description = (
        "The gauge has lost its calibration: it reads the reference block wrong, and every "
        "part by the same error."
    )
    remedy = "recalibrate the gauge"

    def affect(self, machine, readings, part):
        readings["ref_mm"] = round(readings["ref_mm"] + 0.006 * self.cycles, 3)


class Inspection(Machine):
    kind = "inspection"
    description = (
        "Final check: a camera looks at each part and a gauge measures it; "
        "the gauge also reads a 25.000 mm reference block."
    )
    cycle_s = 20
    event = "INSPECT"
    signals = {"image_score": Signal(0.90, 0.99, decimals=2), "ref_mm": Signal(24.995, 25.005, decimals=3)}
    measures = {"dim_mm": Signal(NOMINAL_MM - TOLERANCE_MM, NOMINAL_MM + TOLERANCE_MM, decimals=3)}
    faults = [DirtyLens, GaugeDrift]

    def work(self, part, readings, t):
        # The gauge makes the same error on the part as on the reference block.
        error = readings["ref_mm"] - REFERENCE_MM
        measured = part.dimension_mm + error + self.rng.gauss(0, 0.002)
        readings["dim_mm"] = round(measured, 3)
        good = abs(measured - NOMINAL_MM) <= TOLERANCE_MM and readings["image_score"] >= MIN_IMAGE_SCORE
        part.status = "ok" if good else "rejected"
        readings["result"] = "OK" if good else "REJECT"
