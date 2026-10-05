# Ibis R-83 robot arm (cell 2B)

## Overview {#robot2-overview}

The Ibis R-83 is a robot arm in cell 2B. It was installed in 2023 and runs two shifts a day. Before a run, check that the cabinet fan is running and that the cell fence gate is closed. Service extension: 472.

## Approved materials {#robot2-materials}

Approved materials for the Ibis R-83: boxed parts, metal brackets and plastic housings. Never process open containers of liquid: they spill on the controller. The largest part is 150 × 250 mm.

## Operating settings {#robot2-settings}

The nominal payload of the Ibis R-83 is 10 kg. The allowed range is 8–12 kg. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the joint 3 gearbox.

## Cooling {#robot2-cooling}

The cabinet fan keeps the joint 3 gearbox between 20 and 28 °C. Above 34 °C the machine stops with code E-6123. Check the cabinet fan every 14 days.

## Error codes {#robot2-errors}

E-6123: the joint 3 gearbox is above its limit of 77 °C. Let it cool for 15 minutes before a restart.
E-6132: drive overcurrent on axis X. Remove any jam, then restart.
E-6213: sensor S40 does not respond. Check its cable at terminal X10.
E-6231: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-6312: the cell fence gate interlock opened during a run. Close the cell fence gate and press RESET.
E-6321: the cabinet fan is not running. Check its fuse F4 and its connector.

## Maintenance schedule {#robot2-maintenance}

Every day, check the cell fence gate interlock. Every 250 operating hours, clean the cabinet fan filter. Every 750 operating hours, grease the encoder battery mount with grease GR-4.

## Spare parts {#robot2-parts}

PN-X2V-991-A: encoder battery.
PN-X2V-991-B: joint 3 gearbox.
PN-X2V-919-A: teach pendant cable.
PN-X2V-919-B: brake module.
PN-X2V-199-A: gripper finger.
PN-X2V-199-B: vacuum cup.

## Troubleshooting {#robot2-troubleshooting}

The joint 3 gearbox gets too hot after long runs: the cabinet fan filter is clogged. Clean it.
The payload drifts during a job: sensor S40 needs calibration. Use calibration tool CT-37.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#robot2-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-58 and hang your own lock. Two people are needed to replace the joint 3 gearbox.

## Installation requirements {#robot2-installation}

The Ibis R-83 needs a 230 V supply protected by a 32 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 13 and 29 °C, with a relative humidity below 60%.

## Start-up procedure {#robot2-startup}

1. Check that the cell fence gate is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the cabinet fan and wait until the joint 3 gearbox is below 28 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P376 for a test run, and check the first part before you start a batch.

## Calibration {#robot2-calibration}

Calibrate the Ibis R-83 every 2 months, and after any crash or part replacement. Use calibration tool CT-37 and the reference block RB-257. The measured payload must be within ±3% of the set value; if it is not, adjust offset parameter K11 and repeat. Write the result in the machine log.
