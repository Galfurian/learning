# Tamarin C-83 belt conveyor (cell 5D)

## Overview {#conveyor4-overview}

The Tamarin C-83 is a belt conveyor in cell 5D. It was installed in 2016 and runs three shifts a day. Before a run, check that the motor fan is running and that the side guards is closed. Service extension: 365.

## Approved materials {#conveyor4-materials}

Approved materials for the Tamarin C-83: totes, trays and boxed parts. Never process parts over 25 kg: they overload the belt. The largest part is 100 × 250 mm.

## Operating settings {#conveyor4-settings}

The nominal belt speed of the Tamarin C-83 is 32 m/min. The allowed range is 22–42 m/min. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the drive motor.

## Cooling {#conveyor4-cooling}

The motor fan keeps the drive motor between 19 and 28 °C. Above 35 °C the machine stops with code E-5130. Check the motor fan every 7 days.

## Error codes {#conveyor4-errors}

E-5013: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-5031: the side guards interlock opened during a run. Close the side guards and press RESET.
E-5103: drive overcurrent on axis X. Remove any jam, then restart.
E-5130: the drive motor is above its limit of 84 °C. Let it cool for 15 minutes before a restart.
E-5301: the motor fan is not running. Check its fuse F2 and its connector.
E-5310: sensor S42 does not respond. Check its cable at terminal X19.

## Maintenance schedule {#conveyor4-maintenance}

Every day, check the side guards interlock. Every 100 operating hours, clean the motor fan filter. Every 500 operating hours, grease the gearbox mount with grease GR-5.

## Spare parts {#conveyor4-parts}

PN-X4T-991-A: gearbox.
PN-X4T-991-B: pull-cord switch.
PN-X4T-199-A: drive roller.
PN-X4T-199-B: belt.
PN-X4T-919-A: photo eye.
PN-X4T-919-B: idler roller.

## Troubleshooting {#conveyor4-troubleshooting}

The drive motor gets too hot after long runs: the motor fan filter is clogged. Clean it.
The belt speed drifts during a job: sensor S42 needs calibration. Use calibration tool CT-96.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#conveyor4-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-10 and hang your own lock. Two people are needed to replace the pull-cord switch.

## Installation requirements {#conveyor4-installation}

The Tamarin C-83 needs a 230 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 700 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 13 and 29 °C, with a relative humidity below 80%.

## Start-up procedure {#conveyor4-startup}

1. Check that the side guards is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the motor fan and wait until the drive motor is below 28 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P637 for a test run, and check the first part before you start a batch.

## Calibration {#conveyor4-calibration}

Calibrate the Tamarin C-83 every 6 months, and after any crash or part replacement. Use calibration tool CT-96 and the reference block RB-432. The measured belt speed must be within ±5% of the set value; if it is not, adjust offset parameter K20 and repeat. Write the result in the machine log.
