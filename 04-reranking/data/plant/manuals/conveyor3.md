# Tamarin C-70 belt conveyor (cell 4C)

## Overview {#conveyor3-overview}

The Tamarin C-70 is a belt conveyor in cell 4C. It was installed in 2022 and runs one shifts a day. Before a run, check that the motor fan is running and that the side guards is closed. Service extension: 262.

## Approved materials {#conveyor3-materials}

Approved materials for the Tamarin C-70: boxed parts, totes and trays. Never process loose bulk material: it jams the rollers. The largest part is 300 × 100 mm.

## Operating settings {#conveyor3-settings}

The nominal belt speed of the Tamarin C-70 is 52 m/min. The allowed range is 42–62 m/min. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the drive motor.

## Cooling {#conveyor3-cooling}

The motor fan keeps the drive motor between 19 and 26 °C. Above 29 °C the machine stops with code E-5203. Check the motor fan every 7 days.

## Error codes {#conveyor3-errors}

E-5023: drive overcurrent on axis Y. Remove any jam, then restart.
E-5032: sensor S31 does not respond. Check its cable at terminal X7.
E-5203: the drive motor is above its limit of 64 °C. Let it cool for 10 minutes before a restart.
E-5230: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-5302: the motor fan is not running. Check its fuse F1 and its connector.
E-5320: the side guards interlock opened during a run. Close the side guards and press RESET.

## Maintenance schedule {#conveyor3-maintenance}

Every day, check the side guards interlock. Every 150 operating hours, clean the motor fan filter. Every 750 operating hours, grease the gearbox mount with grease GR-2.

## Spare parts {#conveyor3-parts}

PN-X3T-991-A: gearbox.
PN-X3T-991-B: idler roller.
PN-X3T-199-A: belt.
PN-X3T-199-B: drive roller.
PN-X3T-919-A: photo eye.
PN-X3T-919-B: pull-cord switch.

## Troubleshooting {#conveyor3-troubleshooting}

The drive motor gets too hot after long runs: the motor fan filter is clogged. Clean it.
The belt speed drifts during a job: sensor S31 needs calibration. Use calibration tool CT-89.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#conveyor3-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-24 and hang your own lock. Two people are needed to replace the idler roller.

## Installation requirements {#conveyor3-installation}

The Tamarin C-70 needs a 230 V supply protected by a 25 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 800 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 10 and 33 °C, with a relative humidity below 70%.

## Start-up procedure {#conveyor3-startup}

1. Check that the side guards is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the motor fan and wait until the drive motor is below 26 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P989 for a test run, and check the first part before you start a batch.

## Calibration {#conveyor3-calibration}

Calibrate the Tamarin C-70 every 1 months, and after any crash or part replacement. Use calibration tool CT-89 and the reference block RB-215. The measured belt speed must be within ±1% of the set value; if it is not, adjust offset parameter K31 and repeat. Write the result in the machine log.
