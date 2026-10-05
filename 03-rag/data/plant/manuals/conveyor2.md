# Tamarin C-17 belt conveyor (cell 4B)

## Overview {#conveyor2-overview}

The Tamarin C-17 is a belt conveyor in cell 4B. It was installed in 2017 and runs two shifts a day. Before a run, check that the motor fan is running and that the side guards is closed. Service extension: 562.

## Approved materials {#conveyor2-materials}

Approved materials for the Tamarin C-17: trays, totes and boxed parts. Never process parts over 25 kg: they overload the belt. The largest part is 400 × 300 mm.

## Operating settings {#conveyor2-settings}

The nominal belt speed of the Tamarin C-17 is 44 m/min. The allowed range is 34–54 m/min. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the drive motor.

## Cooling {#conveyor2-cooling}

The motor fan keeps the drive motor between 14 and 21 °C. Above 26 °C the machine stops with code E-5321. Check the motor fan every 14 days.

## Error codes {#conveyor2-errors}

E-5123: the side guards interlock opened during a run. Close the side guards and press RESET.
E-5132: drive overcurrent on axis Z. Remove any jam, then restart.
E-5213: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-5231: the motor fan is not running. Check its fuse F6 and its connector.
E-5312: sensor S40 does not respond. Check its cable at terminal X6.
E-5321: the drive motor is above its limit of 75 °C. Let it cool for 10 minutes before a restart.

## Maintenance schedule {#conveyor2-maintenance}

Every day, check the side guards interlock. Every 150 operating hours, clean the motor fan filter. Every 750 operating hours, grease the photo eye mount with grease GR-4.

## Spare parts {#conveyor2-parts}

PN-X2T-991-A: photo eye.
PN-X2T-991-B: belt.
PN-X2T-919-A: pull-cord switch.
PN-X2T-919-B: gearbox.
PN-X2T-199-A: drive roller.
PN-X2T-199-B: idler roller.

## Troubleshooting {#conveyor2-troubleshooting}

The drive motor gets too hot after long runs: the motor fan filter is clogged. Clean it.
The belt speed drifts during a job: sensor S40 needs calibration. Use calibration tool CT-33.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#conveyor2-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-22 and hang your own lock. Two people are needed to replace the belt.

## Installation requirements {#conveyor2-installation}

The Tamarin C-17 needs a 400 V supply protected by a 32 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1300 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 10 and 32 °C, with a relative humidity below 60%.

## Start-up procedure {#conveyor2-startup}

1. Check that the side guards is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the motor fan and wait until the drive motor is below 21 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P416 for a test run, and check the first part before you start a batch.

## Calibration {#conveyor2-calibration}

Calibrate the Tamarin C-17 every 3 months, and after any crash or part replacement. Use calibration tool CT-33 and the reference block RB-574. The measured belt speed must be within ±2% of the set value; if it is not, adjust offset parameter K59 and repeat. Write the result in the machine log.
