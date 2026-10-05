# Kestrel LX-57 laser cutter (cell 2C)

## Overview {#laser3-overview}

The Kestrel LX-57 is a laser cutter in cell 2C. It was installed in 2024 and runs two shifts a day. Before a run, check that the water chiller is running and that the lid is closed. Service extension: 340.

## Approved materials {#laser3-materials}

Approved materials for the Kestrel LX-57: cork, acrylic and birch plywood. Never process polycarbonate: it catches fire. The largest part is 150 × 300 mm.

## Operating settings {#laser3-settings}

The nominal power of the Kestrel LX-57 is 78 %. The allowed range is 63–93 %. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the laser tube.

## Cooling {#laser3-cooling}

The water chiller keeps the laser tube between 19 and 25 °C. Above 33 °C the machine stops with code E-4203. Check the water chiller every 3 days.

## Error codes {#laser3-errors}

E-4023: the lid interlock opened during a run. Close the lid and press RESET.
E-4032: drive overcurrent on axis X. Remove any jam, then restart.
E-4203: the laser tube is above its limit of 70 °C. Let it cool for 20 minutes before a restart.
E-4230: sensor S13 does not respond. Check its cable at terminal X6.
E-4302: the water chiller is not running. Check its fuse F5 and its connector.
E-4320: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.

## Maintenance schedule {#laser3-maintenance}

Every day, check the lid interlock. Every 150 operating hours, clean the water chiller filter. Every 1500 operating hours, grease the focus lens mount with grease GR-1.

## Spare parts {#laser3-parts}

PN-X3Q-991-A: focus lens.
PN-X3Q-991-B: honeycomb bed.
PN-X3Q-199-A: nozzle cone.
PN-X3Q-199-B: air filter.
PN-X3Q-919-A: first mirror.
PN-X3Q-919-B: second mirror.

## Troubleshooting {#laser3-troubleshooting}

The laser tube gets too hot after long runs: the water chiller filter is clogged. Clean it.
The power drifts during a job: sensor S13 needs calibration. Use calibration tool CT-31.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#laser3-safety}

Wear laser safety glasses. Before maintenance, lock out breaker CB-19 and hang your own lock. Two people are needed to replace the honeycomb bed.

## Installation requirements {#laser3-installation}

The Kestrel LX-57 needs a 400 V supply protected by a 20 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 14 and 35 °C, with a relative humidity below 70%.

## Start-up procedure {#laser3-startup}

1. Check that the lid is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the water chiller and wait until the laser tube is below 25 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P383 for a test run, and check the first part before you start a batch.

## Calibration {#laser3-calibration}

Calibrate the Kestrel LX-57 every 2 months, and after any crash or part replacement. Use calibration tool CT-31 and the reference block RB-277. The measured power must be within ±1% of the set value; if it is not, adjust offset parameter K30 and repeat. Write the result in the machine log.
