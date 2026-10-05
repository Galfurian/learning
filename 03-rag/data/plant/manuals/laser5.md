# Kestrel LX-27 laser cutter (cell 9E)

## Overview {#laser5-overview}

The Kestrel LX-27 is a laser cutter in cell 9E. It was installed in 2021 and runs three shifts a day. Before a run, check that the water chiller is running and that the lid is closed. Service extension: 283.

## Approved materials {#laser5-materials}

Approved materials for the Kestrel LX-27: cardboard, acrylic and cork. Never process PVC: it releases chlorine gas. The largest part is 250 × 100 mm.

## Operating settings {#laser5-settings}

The nominal power of the Kestrel LX-27 is 81 %. The allowed range is 66–96 %. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the laser tube.

## Cooling {#laser5-cooling}

The water chiller keeps the laser tube between 14 and 19 °C. Above 26 °C the machine stops with code E-4124. Check the water chiller every 5 days.

## Error codes {#laser5-errors}

E-4124: the laser tube is above its limit of 84 °C. Let it cool for 30 minutes before a restart.
E-4142: the lid interlock opened during a run. Close the lid and press RESET.
E-4214: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-4241: sensor S16 does not respond. Check its cable at terminal X12.
E-4412: the water chiller is not running. Check its fuse F3 and its connector.
E-4421: drive overcurrent on axis X. Remove any jam, then restart.

## Maintenance schedule {#laser5-maintenance}

Every day, check the lid interlock. Every 250 operating hours, clean the water chiller filter. Every 750 operating hours, grease the focus lens mount with grease GR-1.

## Spare parts {#laser5-parts}

PN-X5Q-991-A: focus lens.
PN-X5Q-991-B: honeycomb bed.
PN-X5Q-199-A: air filter.
PN-X5Q-199-B: nozzle cone.
PN-X5Q-919-A: second mirror.
PN-X5Q-919-B: first mirror.

## Troubleshooting {#laser5-troubleshooting}

The laser tube gets too hot after long runs: the water chiller filter is clogged. Clean it.
The power drifts during a job: sensor S16 needs calibration. Use calibration tool CT-67.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#laser5-safety}

Wear laser safety glasses. Before maintenance, lock out breaker CB-49 and hang your own lock. Two people are needed to replace the honeycomb bed.

## Installation requirements {#laser5-installation}

The Kestrel LX-27 needs a 230 V supply protected by a 16 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1000 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 12 and 35 °C, with a relative humidity below 70%.

## Start-up procedure {#laser5-startup}

1. Check that the lid is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the water chiller and wait until the laser tube is below 19 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P160 for a test run, and check the first part before you start a batch.

## Calibration {#laser5-calibration}

Calibrate the Kestrel LX-27 every 3 months, and after any crash or part replacement. Use calibration tool CT-67 and the reference block RB-235. The measured power must be within ±3% of the set value; if it is not, adjust offset parameter K14 and repeat. Write the result in the machine log.
