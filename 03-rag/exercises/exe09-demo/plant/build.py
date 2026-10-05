"""Write the plant manuals: invented machines with many look-alike identifiers.

    uv run python exercises/exe09-demo/plant/build.py

Deterministic: the same SEED always writes the same files. Machines of the
same type share their templates, so their manuals are near-duplicates that
differ in values, codes and part numbers. That is the hard case for retrieval.
"""

import itertools
import random

from raglab.context import estimate_tokens
from raglab.corpus import PLANT_MANUALS, load_manuals

SEED = 9
UNITS_PER_TYPE = 5

# key, type name, family, part letter, error digit, vocabulary
TYPES = [
    ("laser", "laser cutter", "Kestrel LX", "Q", 4, dict(
        component="laser tube", coolant="water chiller", guard="lid", param="power", unit=" %",
        nominal=(60, 90), span=15, ppe="laser safety glasses",
        materials=["acrylic", "birch plywood", "cardboard", "felt", "cork"],
        forbidden=[("PVC", "it releases chlorine gas"), ("polycarbonate", "it catches fire")],
        parts=["focus lens", "first mirror", "second mirror", "nozzle cone", "air filter", "honeycomb bed"])),
    ("printer", "3D printer", "Bramble P", "R", 2, dict(
        component="hotend", coolant="hotend fan", guard="enclosure door", param="nozzle temperature", unit=" °C",
        nominal=(200, 250), span=15, ppe="heat-resistant gloves",
        materials=["PLA", "PETG", "TPU", "ASA", "nylon"],
        forbidden=[("PEEK", "the hotend cannot reach its temperature"), ("carbon-filled filament", "it wears the brass nozzle")],
        parts=["nozzle", "heater cartridge", "thermistor", "build sheet", "extruder gear", "Z lead screw"])),
    ("oven", "reflow oven", "Corvid RF", "S", 7, dict(
        component="heater bank", coolant="cooling fan", guard="hood", param="peak temperature", unit=" °C",
        nominal=(235, 250), span=10, ppe="heat-resistant gloves",
        materials=["FR-4 boards", "aluminium core boards", "polyimide flex boards"],
        forbidden=[("boards with unsealed batteries", "they can vent"), ("paper-based boards", "they char")],
        parts=["zone heater", "thermocouple", "convection fan motor", "conveyor mesh", "door seal", "exhaust damper"])),
    ("conveyor", "belt conveyor", "Tamarin C", "T", 5, dict(
        component="drive motor", coolant="motor fan", guard="side guards", param="belt speed", unit=" m/min",
        nominal=(20, 60), span=10, ppe="safety shoes",
        materials=["boxed parts", "trays", "totes"],
        forbidden=[("loose bulk material", "it jams the rollers"), ("parts over 25 kg", "they overload the belt")],
        parts=["drive roller", "idler roller", "belt", "photo eye", "pull-cord switch", "gearbox"])),
    ("mill", "CNC mill", "Heron M", "U", 3, dict(
        component="spindle", coolant="coolant pump", guard="door", param="spindle speed", unit=" rpm",
        nominal=(8000, 18000), span=2000, ppe="safety glasses",
        materials=["aluminium", "brass", "POM", "mild steel"],
        forbidden=[("magnesium", "its chips can ignite"), ("glass-filled plastics", "they wear the tools fast")],
        parts=["tool holder", "spindle belt", "way cover", "coolant nozzle", "probe stylus", "chip auger"])),
    ("robot", "robot arm", "Ibis R", "V", 6, dict(
        component="joint 3 gearbox", coolant="cabinet fan", guard="cell fence gate", param="payload", unit=" kg",
        nominal=(5, 12), span=2, ppe="safety shoes",
        materials=["metal brackets", "plastic housings", "boxed parts"],
        forbidden=[("loads over the rated payload", "they damage the gearboxes"), ("open containers of liquid", "they spill on the controller")],
        parts=["gripper finger", "vacuum cup", "joint 3 gearbox", "teach pendant cable", "brake module", "encoder battery"])),
    ("vision", "vision inspection station", "Lynx V", "W", 8, dict(
        component="camera", coolant="light bar fan", guard="light shield", param="exposure time", unit=" ms",
        nominal=(2, 12), span=2, ppe="no special equipment",
        materials=["painted parts", "machined parts", "printed labels"],
        forbidden=[("mirror-polished parts", "the reflections blind the camera"), ("transparent parts", "their edges are not visible")],
        parts=["camera lens", "ring light", "light bar", "calibration target", "trigger sensor", "lens cover"])),
    ("sealer", "packaging sealer", "Marten S", "Y", 9, dict(
        component="sealing jaw", coolant="jaw cooling air", guard="front guard", param="jaw temperature", unit=" °C",
        nominal=(140, 190), span=15, ppe="heat-resistant gloves",
        materials=["PE film", "PP film", "laminated film"],
        forbidden=[("PVC film", "it releases fumes"), ("foil laminates without a sealant layer", "they do not seal")],
        parts=["sealing jaw", "Teflon tape", "film knife", "heater element", "pressure spring", "film roller"])),
]

FAULTS = [
    "the {guard} interlock opened during a run. Close the {guard} and press RESET.",
    "the {coolant} is not running. Check its fuse F{fuse} and its connector.",
    "the {component} is above its limit of {limit} °C. Let it cool for {minutes} minutes before a restart.",
    "drive overcurrent on axis {axis}. Remove any jam, then restart.",
    "sensor S{sensor} does not respond. Check its cable at terminal X{terminal}.",
    "the air pressure is below {pressure} bar. Check the supply hose and the inline filter.",
]
DIGIT_SETS = [(0, 1, 2), (1, 2, 3), (0, 2, 3), (0, 1, 3), (1, 2, 4), (0, 3, 4)]


def manual(rng: random.Random, key: str, type_name: str, family: str, letter: str, digit: int, v: dict,
           unit: int, number: int) -> str:
    mid = f"{key}{unit}"
    name = f"{family}-{number}"
    cell = f"{rng.randint(1, 9)}{'ABCDEF'[unit - 1]}"
    lo_nom, hi_nom = v["nominal"]
    nominal = rng.randrange(lo_nom, hi_nom + 1, max(1, (hi_nom - lo_nom) // 10 or 1))
    low, high = nominal - v["span"], nominal + v["span"]
    t1 = rng.randint(14, 20)
    t2 = t1 + rng.randint(5, 9)
    codes = ["E-" + str(digit) + "".join(map(str, p)) for p in itertools.permutations(DIGIT_SETS[unit - 1])]
    faults = rng.sample(FAULTS, len(FAULTS))
    values = dict(fuse=rng.randint(1, 9), limit=rng.randint(60, 95), minutes=rng.choice([10, 15, 20, 30]),
                  axis=rng.choice("XYZ"), sensor=rng.randint(10, 49), terminal=rng.randint(1, 24),
                  pressure=rng.choice([1.5, 2.0, 2.5, 3.0]), tool=rng.randint(10, 99), **v)
    numbers = rng.sample(["991", "919", "199"], 3)
    pns = [f"PN-X{unit}{letter}-{n}-{s}" for n in numbers for s in "AB"]
    parts = rng.sample(v["parts"], len(v["parts"]))
    material = rng.sample(v["materials"], min(3, len(v["materials"])))
    forbidden, reason = rng.choice(v["forbidden"])
    h1, h2 = rng.choice([100, 150, 200, 250]), rng.choice([500, 750, 1000, 1500])
    sections = {
        "overview": (
            "Overview",
            f"The {name} is a {type_name} in cell {cell}. It was installed in {rng.randint(2016, 2025)} and runs "
            f"{rng.choice(['one', 'two', 'three'])} shifts a day. Before a run, check that the {v['coolant']} is "
            f"running and that the {v['guard']} is closed. Service extension: {rng.randint(200, 899)}."),
        "materials": (
            "Approved materials",
            f"Approved materials for the {name}: {', '.join(material[:-1])} and {material[-1]}. "
            f"Never process {forbidden}: {reason}. The largest part is {rng.randint(2, 9) * 50} × {rng.randint(2, 6) * 50} mm."),
        "settings": (
            "Operating settings",
            f"The nominal {v['param']} of the {name} is {nominal}{v['unit']}. The allowed range is {low}–{high}{v['unit']}. "
            f"Change it only between jobs. At the upper limit, lower the feed by {rng.choice([10, 15, 20, 25])}% "
            f"to protect the {v['component']}."),
        "cooling": (
            "Cooling",
            f"The {v['coolant']} keeps the {v['component']} between {t1} and {t2} °C. Above {t2 + rng.randint(3, 8)} °C "
            f"the machine stops with code {codes[faults.index(FAULTS[2])]}. Check the {v['coolant']} every "
            f"{rng.choice([3, 5, 7, 14])} days."),
        "errors": (
            "Error codes",
            "\n".join(f"{code}: {fault.format(**values)}" for code, fault in zip(codes, faults))),
        "maintenance": (
            "Maintenance schedule",
            f"Every day, check the {v['guard']} interlock. Every {h1} operating hours, clean the {v['coolant']} filter. "
            f"Every {h2} operating hours, grease the {parts[0]} mount with grease GR-{rng.randint(1, 5)}."),
        "parts": (
            "Spare parts",
            "\n".join(f"{pn}: {part}." for pn, part in zip(pns, parts))),
        "troubleshooting": (
            "Troubleshooting",
            f"The {v['component']} gets too hot after long runs: the {v['coolant']} filter is clogged. Clean it.\n"
            f"The {v['param']} drifts during a job: sensor S{values['sensor']} needs calibration. Use calibration tool CT-{values['tool']}.\n"
            f"The machine stops without an error code: the emergency stop on the {rng.choice(['left', 'right', 'rear'])} panel is pressed.\n"
            f"Results vary between shifts: the warm-up was skipped. Run the {rng.choice([5, 10, 15])}-minute warm-up before the first job."),
        "safety": (
            "Safety",
            f"Wear {v['ppe']}. Before maintenance, lock out breaker CB-{rng.randint(10, 60)} and hang your own lock. "
            f"Two people are needed to replace the {parts[1]}."),
        "installation": (
            "Installation requirements",
            f"The {name} needs a {rng.choice([230, 400])} V supply protected by a {rng.choice([16, 20, 25, 32])} A breaker, "
            f"and compressed air at {rng.choice([5, 6, 7])} bar if the air option is fitted. The floor must carry "
            f"{rng.randint(4, 15) * 100} kg per square metre. Keep {rng.choice([50, 60, 80, 100])} cm free on every side "
            f"for service access. The room must stay between {rng.randint(10, 15)} and {rng.randint(28, 35)} °C, "
            f"with a relative humidity below {rng.choice([60, 70, 80])}%."),
        "startup": (
            "Start-up procedure",
            f"1. Check that the {v['guard']} is closed and that nothing is left inside the work area.\n"
            f"2. Switch on the main isolator and wait {rng.choice([20, 30, 45, 60])} s for the controller to boot.\n"
            f"3. Start the {v['coolant']} and wait until the {v['component']} is below {t2} °C.\n"
            f"4. Run the homing cycle from the operator panel. It takes about {rng.choice([2, 3, 4])} minutes.\n"
            f"5. Load program P{rng.randint(100, 999)} for a test run, and check the first part before you start a batch."),
        "calibration": (
            "Calibration",
            f"Calibrate the {name} every {rng.choice([1, 2, 3, 6])} months, and after any crash or part replacement. "
            f"Use calibration tool CT-{values['tool']} and the reference block RB-{rng.randint(100, 999)}. "
            f"The measured {v['param']} must be within ±{rng.choice([1, 2, 3, 5])}% of the set value; if it is not, "
            f"adjust offset parameter K{rng.randint(10, 99)} and repeat. Write the result in the machine log."),
    }
    lines = [f"# {name} {type_name} (cell {cell})", ""]
    for topic, (title, text) in sections.items():
        lines += [f"## {title} {{#{mid}-{topic}}}", "", text, ""]
    return "\n".join(lines)


def main() -> None:
    rng = random.Random(SEED)
    PLANT_MANUALS.mkdir(parents=True, exist_ok=True)
    for old in PLANT_MANUALS.glob("*.md"):
        old.unlink()
    for key, type_name, family, letter, digit, vocabulary in TYPES:
        numbers = rng.sample(range(10, 100), UNITS_PER_TYPE)  # display names unique within a type
        for unit, number in enumerate(numbers, start=1):
            text = manual(rng, key, type_name, family, letter, digit, vocabulary, unit, number)
            (PLANT_MANUALS / f"{key}{unit}.md").write_text(text, encoding="utf-8")
    sections = load_manuals(PLANT_MANUALS)
    tokens = sum(estimate_tokens(s.text) for s in sections)
    print(f"{len(sections)} sections in {PLANT_MANUALS}, about {tokens} tokens")


if __name__ == "__main__":
    main()
