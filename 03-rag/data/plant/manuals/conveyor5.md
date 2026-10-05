# Tamarin C-36 belt conveyor (cell 1E)

## Overview {#conveyor5-overview}

The Tamarin C-36 is a belt conveyor in cell 1E. It was installed in 2021 and runs three shifts a day. Before a run, check that the motor fan is running and that the side guards is closed. Service extension: 706.

## Approved materials {#conveyor5-materials}

Approved materials for the Tamarin C-36: boxed parts, trays and totes. Never process loose bulk material: it jams the rollers. The largest part is 400 × 200 mm.

## Operating settings {#conveyor5-settings}

The nominal belt speed of the Tamarin C-36 is 36 m/min. The allowed range is 26–46 m/min. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the drive motor.

## Cooling {#conveyor5-cooling}

The motor fan keeps the drive motor between 14 and 19 °C. Above 24 °C the machine stops with code E-5214. Check the motor fan every 3 days.

## Error codes {#conveyor5-errors}

E-5124: the side guards interlock opened during a run. Close the side guards and press RESET.
E-5142: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-5214: the drive motor is above its limit of 64 °C. Let it cool for 10 minutes before a restart.
E-5241: the motor fan is not running. Check its fuse F7 and its connector.
E-5412: drive overcurrent on axis Z. Remove any jam, then restart.
E-5421: sensor S48 does not respond. Check its cable at terminal X4.

## Maintenance schedule {#conveyor5-maintenance}

Every day, check the side guards interlock. Every 200 operating hours, clean the motor fan filter. Every 1000 operating hours, grease the drive roller mount with grease GR-3.

## Spare parts {#conveyor5-parts}

PN-X5T-991-A: drive roller.
PN-X5T-991-B: idler roller.
PN-X5T-199-A: pull-cord switch.
PN-X5T-199-B: gearbox.
PN-X5T-919-A: photo eye.
PN-X5T-919-B: belt.

## Troubleshooting {#conveyor5-troubleshooting}

The drive motor gets too hot after long runs: the motor fan filter is clogged. Clean it.
The belt speed drifts during a job: sensor S48 needs calibration. Use calibration tool CT-30.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#conveyor5-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-21 and hang your own lock. Two people are needed to replace the idler roller.

## Installation requirements {#conveyor5-installation}

The Tamarin C-36 needs a 400 V supply protected by a 20 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 13 and 33 °C, with a relative humidity below 80%.

## Start-up procedure {#conveyor5-startup}

1. Check that the side guards is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the motor fan and wait until the drive motor is below 19 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P836 for a test run, and check the first part before you start a batch.

## Calibration {#conveyor5-calibration}

Calibrate the Tamarin C-36 every 1 months, and after any crash or part replacement. Use calibration tool CT-30 and the reference block RB-368. The measured belt speed must be within ±5% of the set value; if it is not, adjust offset parameter K12 and repeat. Write the result in the machine log.
