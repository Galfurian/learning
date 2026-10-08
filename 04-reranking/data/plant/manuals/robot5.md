# Ibis R-99 robot arm (cell 2E)

## Overview {#robot5-overview}

The Ibis R-99 is a robot arm in cell 2E. It was installed in 2024 and runs one shifts a day. Before a run, check that the cabinet fan is running and that the cell fence gate is closed. Service extension: 392.

## Approved materials {#robot5-materials}

Approved materials for the Ibis R-99: metal brackets, plastic housings and boxed parts. Never process loads over the rated payload: they damage the gearboxes. The largest part is 200 × 250 mm.

## Operating settings {#robot5-settings}

The nominal payload of the Ibis R-99 is 11 kg. The allowed range is 9–13 kg. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the joint 3 gearbox.

## Cooling {#robot5-cooling}

The cabinet fan keeps the joint 3 gearbox between 19 and 28 °C. Above 34 °C the machine stops with code E-6124. Check the cabinet fan every 7 days.

## Error codes {#robot5-errors}

E-6124: the joint 3 gearbox is above its limit of 74 °C. Let it cool for 10 minutes before a restart.
E-6142: the cell fence gate interlock opened during a run. Close the cell fence gate and press RESET.
E-6214: drive overcurrent on axis Z. Remove any jam, then restart.
E-6241: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-6412: sensor S20 does not respond. Check its cable at terminal X10.
E-6421: the cabinet fan is not running. Check its fuse F4 and its connector.

## Maintenance schedule {#robot5-maintenance}

Every day, check the cell fence gate interlock. Every 150 operating hours, clean the cabinet fan filter. Every 750 operating hours, grease the teach pendant cable mount with grease GR-3.

## Spare parts {#robot5-parts}

PN-X5V-199-A: teach pendant cable.
PN-X5V-199-B: brake module.
PN-X5V-919-A: vacuum cup.
PN-X5V-919-B: gripper finger.
PN-X5V-991-A: encoder battery.
PN-X5V-991-B: joint 3 gearbox.

## Troubleshooting {#robot5-troubleshooting}

The joint 3 gearbox gets too hot after long runs: the cabinet fan filter is clogged. Clean it.
The payload drifts during a job: sensor S20 needs calibration. Use calibration tool CT-33.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#robot5-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-24 and hang your own lock. Two people are needed to replace the brake module.

## Installation requirements {#robot5-installation}

The Ibis R-99 needs a 400 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1400 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 15 and 35 °C, with a relative humidity below 70%.

## Start-up procedure {#robot5-startup}

1. Check that the cell fence gate is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the cabinet fan and wait until the joint 3 gearbox is below 28 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P198 for a test run, and check the first part before you start a batch.

## Calibration {#robot5-calibration}

Calibrate the Ibis R-99 every 1 months, and after any crash or part replacement. Use calibration tool CT-33 and the reference block RB-747. The measured payload must be within ±1% of the set value; if it is not, adjust offset parameter K77 and repeat. Write the result in the machine log.
