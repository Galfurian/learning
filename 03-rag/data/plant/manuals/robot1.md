# Ibis R-82 robot arm (cell 1A)

## Overview {#robot1-overview}

The Ibis R-82 is a robot arm in cell 1A. It was installed in 2018 and runs two shifts a day. Before a run, check that the cabinet fan is running and that the cell fence gate is closed. Service extension: 562.

## Approved materials {#robot1-materials}

Approved materials for the Ibis R-82: boxed parts, plastic housings and metal brackets. Never process open containers of liquid: they spill on the controller. The largest part is 350 × 150 mm.

## Operating settings {#robot1-settings}

The nominal payload of the Ibis R-82 is 9 kg. The allowed range is 7–11 kg. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the joint 3 gearbox.

## Cooling {#robot1-cooling}

The cabinet fan keeps the joint 3 gearbox between 14 and 22 °C. Above 30 °C the machine stops with code E-6120. Check the cabinet fan every 7 days.

## Error codes {#robot1-errors}

E-6012: drive overcurrent on axis Z. Remove any jam, then restart.
E-6021: the cabinet fan is not running. Check its fuse F1 and its connector.
E-6102: sensor S17 does not respond. Check its cable at terminal X18.
E-6120: the joint 3 gearbox is above its limit of 78 °C. Let it cool for 10 minutes before a restart.
E-6201: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-6210: the cell fence gate interlock opened during a run. Close the cell fence gate and press RESET.

## Maintenance schedule {#robot1-maintenance}

Every day, check the cell fence gate interlock. Every 100 operating hours, clean the cabinet fan filter. Every 500 operating hours, grease the joint 3 gearbox mount with grease GR-4.

## Spare parts {#robot1-parts}

PN-X1V-991-A: joint 3 gearbox.
PN-X1V-991-B: vacuum cup.
PN-X1V-199-A: brake module.
PN-X1V-199-B: encoder battery.
PN-X1V-919-A: gripper finger.
PN-X1V-919-B: teach pendant cable.

## Troubleshooting {#robot1-troubleshooting}

The joint 3 gearbox gets too hot after long runs: the cabinet fan filter is clogged. Clean it.
The payload drifts during a job: sensor S17 needs calibration. Use calibration tool CT-48.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#robot1-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-16 and hang your own lock. Two people are needed to replace the vacuum cup.

## Installation requirements {#robot1-installation}

The Ibis R-82 needs a 230 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1000 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 15 and 32 °C, with a relative humidity below 60%.

## Start-up procedure {#robot1-startup}

1. Check that the cell fence gate is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the cabinet fan and wait until the joint 3 gearbox is below 22 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P354 for a test run, and check the first part before you start a batch.

## Calibration {#robot1-calibration}

Calibrate the Ibis R-82 every 2 months, and after any crash or part replacement. Use calibration tool CT-48 and the reference block RB-582. The measured payload must be within ±1% of the set value; if it is not, adjust offset parameter K80 and repeat. Write the result in the machine log.
