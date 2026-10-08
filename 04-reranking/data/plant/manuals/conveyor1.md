# Tamarin C-66 belt conveyor (cell 3A)

## Overview {#conveyor1-overview}

The Tamarin C-66 is a belt conveyor in cell 3A. It was installed in 2019 and runs one shifts a day. Before a run, check that the motor fan is running and that the side guards is closed. Service extension: 245.

## Approved materials {#conveyor1-materials}

Approved materials for the Tamarin C-66: boxed parts, trays and totes. Never process parts over 25 kg: they overload the belt. The largest part is 100 × 200 mm.

## Operating settings {#conveyor1-settings}

The nominal belt speed of the Tamarin C-66 is 48 m/min. The allowed range is 38–58 m/min. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the drive motor.

## Cooling {#conveyor1-cooling}

The motor fan keeps the drive motor between 15 and 23 °C. Above 29 °C the machine stops with code E-5102. Check the motor fan every 14 days.

## Error codes {#conveyor1-errors}

E-5012: the side guards interlock opened during a run. Close the side guards and press RESET.
E-5021: drive overcurrent on axis X. Remove any jam, then restart.
E-5102: the drive motor is above its limit of 66 °C. Let it cool for 10 minutes before a restart.
E-5120: sensor S14 does not respond. Check its cable at terminal X12.
E-5201: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-5210: the motor fan is not running. Check its fuse F8 and its connector.

## Maintenance schedule {#conveyor1-maintenance}

Every day, check the side guards interlock. Every 200 operating hours, clean the motor fan filter. Every 750 operating hours, grease the pull-cord switch mount with grease GR-3.

## Spare parts {#conveyor1-parts}

PN-X1T-199-A: pull-cord switch.
PN-X1T-199-B: belt.
PN-X1T-919-A: photo eye.
PN-X1T-919-B: idler roller.
PN-X1T-991-A: drive roller.
PN-X1T-991-B: gearbox.

## Troubleshooting {#conveyor1-troubleshooting}

The drive motor gets too hot after long runs: the motor fan filter is clogged. Clean it.
The belt speed drifts during a job: sensor S14 needs calibration. Use calibration tool CT-42.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#conveyor1-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-52 and hang your own lock. Two people are needed to replace the belt.

## Installation requirements {#conveyor1-installation}

The Tamarin C-66 needs a 230 V supply protected by a 25 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 12 and 28 °C, with a relative humidity below 60%.

## Start-up procedure {#conveyor1-startup}

1. Check that the side guards is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the motor fan and wait until the drive motor is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P339 for a test run, and check the first part before you start a batch.

## Calibration {#conveyor1-calibration}

Calibrate the Tamarin C-66 every 1 months, and after any crash or part replacement. Use calibration tool CT-42 and the reference block RB-374. The measured belt speed must be within ±5% of the set value; if it is not, adjust offset parameter K16 and repeat. Write the result in the machine log.
