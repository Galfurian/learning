# Ibis R-79 robot arm (cell 2D)

## Overview {#robot4-overview}

The Ibis R-79 is a robot arm in cell 2D. It was installed in 2016 and runs three shifts a day. Before a run, check that the cabinet fan is running and that the cell fence gate is closed. Service extension: 479.

## Approved materials {#robot4-materials}

Approved materials for the Ibis R-79: plastic housings, metal brackets and boxed parts. Never process open containers of liquid: they spill on the controller. The largest part is 400 × 250 mm.

## Operating settings {#robot4-settings}

The nominal payload of the Ibis R-79 is 5 kg. The allowed range is 3–7 kg. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the joint 3 gearbox.

## Cooling {#robot4-cooling}

The cabinet fan keeps the joint 3 gearbox between 14 and 20 °C. Above 24 °C the machine stops with code E-6310. Check the cabinet fan every 7 days.

## Error codes {#robot4-errors}

E-6013: the cabinet fan is not running. Check its fuse F7 and its connector.
E-6031: sensor S29 does not respond. Check its cable at terminal X17.
E-6103: the cell fence gate interlock opened during a run. Close the cell fence gate and press RESET.
E-6130: drive overcurrent on axis X. Remove any jam, then restart.
E-6301: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-6310: the joint 3 gearbox is above its limit of 83 °C. Let it cool for 10 minutes before a restart.

## Maintenance schedule {#robot4-maintenance}

Every day, check the cell fence gate interlock. Every 100 operating hours, clean the cabinet fan filter. Every 1000 operating hours, grease the gripper finger mount with grease GR-3.

## Spare parts {#robot4-parts}

PN-X4V-919-A: gripper finger.
PN-X4V-919-B: brake module.
PN-X4V-199-A: joint 3 gearbox.
PN-X4V-199-B: teach pendant cable.
PN-X4V-991-A: vacuum cup.
PN-X4V-991-B: encoder battery.

## Troubleshooting {#robot4-troubleshooting}

The joint 3 gearbox gets too hot after long runs: the cabinet fan filter is clogged. Clean it.
The payload drifts during a job: sensor S29 needs calibration. Use calibration tool CT-56.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#robot4-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-47 and hang your own lock. Two people are needed to replace the brake module.

## Installation requirements {#robot4-installation}

The Ibis R-79 needs a 400 V supply protected by a 20 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1100 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 10 and 32 °C, with a relative humidity below 60%.

## Start-up procedure {#robot4-startup}

1. Check that the cell fence gate is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the cabinet fan and wait until the joint 3 gearbox is below 20 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P473 for a test run, and check the first part before you start a batch.

## Calibration {#robot4-calibration}

Calibrate the Ibis R-79 every 2 months, and after any crash or part replacement. Use calibration tool CT-56 and the reference block RB-471. The measured payload must be within ±3% of the set value; if it is not, adjust offset parameter K45 and repeat. Write the result in the machine log.
