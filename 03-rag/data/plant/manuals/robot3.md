# Ibis R-26 robot arm (cell 2C)

## Overview {#robot3-overview}

The Ibis R-26 is a robot arm in cell 2C. It was installed in 2023 and runs three shifts a day. Before a run, check that the cabinet fan is running and that the cell fence gate is closed. Service extension: 498.

## Approved materials {#robot3-materials}

Approved materials for the Ibis R-26: metal brackets, plastic housings and boxed parts. Never process open containers of liquid: they spill on the controller. The largest part is 200 × 300 mm.

## Operating settings {#robot3-settings}

The nominal payload of the Ibis R-26 is 5 kg. The allowed range is 3–7 kg. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the joint 3 gearbox.

## Cooling {#robot3-cooling}

The cabinet fan keeps the joint 3 gearbox between 20 and 28 °C. Above 36 °C the machine stops with code E-6320. Check the cabinet fan every 14 days.

## Error codes {#robot3-errors}

E-6023: the cell fence gate interlock opened during a run. Close the cell fence gate and press RESET.
E-6032: the cabinet fan is not running. Check its fuse F4 and its connector.
E-6203: sensor S25 does not respond. Check its cable at terminal X4.
E-6230: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-6302: drive overcurrent on axis Z. Remove any jam, then restart.
E-6320: the joint 3 gearbox is above its limit of 92 °C. Let it cool for 10 minutes before a restart.

## Maintenance schedule {#robot3-maintenance}

Every day, check the cell fence gate interlock. Every 100 operating hours, clean the cabinet fan filter. Every 1000 operating hours, grease the vacuum cup mount with grease GR-1.

## Spare parts {#robot3-parts}

PN-X3V-199-A: vacuum cup.
PN-X3V-199-B: teach pendant cable.
PN-X3V-991-A: encoder battery.
PN-X3V-991-B: joint 3 gearbox.
PN-X3V-919-A: gripper finger.
PN-X3V-919-B: brake module.

## Troubleshooting {#robot3-troubleshooting}

The joint 3 gearbox gets too hot after long runs: the cabinet fan filter is clogged. Clean it.
The payload drifts during a job: sensor S25 needs calibration. Use calibration tool CT-96.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#robot3-safety}

Wear safety shoes. Before maintenance, lock out breaker CB-38 and hang your own lock. Two people are needed to replace the teach pendant cable.

## Installation requirements {#robot3-installation}

The Ibis R-26 needs a 400 V supply protected by a 20 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 10 and 33 °C, with a relative humidity below 80%.

## Start-up procedure {#robot3-startup}

1. Check that the cell fence gate is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the cabinet fan and wait until the joint 3 gearbox is below 28 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P254 for a test run, and check the first part before you start a batch.

## Calibration {#robot3-calibration}

Calibrate the Ibis R-26 every 2 months, and after any crash or part replacement. Use calibration tool CT-96 and the reference block RB-878. The measured payload must be within ±1% of the set value; if it is not, adjust offset parameter K53 and repeat. Write the result in the machine log.
