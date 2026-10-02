from ..fault import Fault
from ..machine import Machine
from ..signal import Signal


class Jam(Fault):
    description = "Something blocks the belt: transit gets slow and the motor current rises."
    remedy = "clear the obstruction on the belt"
    slowdown = 2.7

    def affect(self, machine, readings, part):
        readings["motor_a"] = round(machine.rng.gauss(9.2, 0.3), 1)


class BeltSlip(Fault):
    description = "The belt slips on the drive drum: transit gets slow and the motor current drops."
    remedy = "tension the belt"
    slowdown = 2.2

    def affect(self, machine, readings, part):
        readings["motor_a"] = round(machine.rng.gauss(2.0, 0.2), 1)


class Conveyor(Machine):
    kind = "conveyor"
    description = "Moves parts from the feeder to the mill on a motor-driven belt."
    cycle_s = 45
    event = "TRANSIT"
    signals = {"motor_a": Signal(3.5, 4.5)}
    faults = [Jam, BeltSlip]
