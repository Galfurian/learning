# Kestrel LX-69 laser cutter (cell 3A)

## Overview {#laser1-overview}

The Kestrel LX-69 is a laser cutter in cell 3A. It was installed in 2016 and runs one shifts a day. Before a run, check that the water chiller is running and that the lid is closed. Service extension: 205.

## Approved materials {#laser1-materials}

Approved materials for the Kestrel LX-69: acrylic, cardboard and cork. Never process polycarbonate: it catches fire. The largest part is 400 × 100 mm.

## Operating settings {#laser1-settings}

The nominal power of the Kestrel LX-69 is 90 %. The allowed range is 75–105 %. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the laser tube.

## Cooling {#laser1-cooling}

The water chiller keeps the laser tube between 14 and 21 °C. Above 27 °C the machine stops with code E-4210. Check the water chiller every 5 days.

## Error codes {#laser1-errors}

E-4012: sensor S20 does not respond. Check its cable at terminal X8.
E-4021: drive overcurrent on axis X. Remove any jam, then restart.
E-4102: the lid interlock opened during a run. Close the lid and press RESET.
E-4120: the water chiller is not running. Check its fuse F3 and its connector.
E-4201: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-4210: the laser tube is above its limit of 88 °C. Let it cool for 30 minutes before a restart.

## Maintenance schedule {#laser1-maintenance}

Every day, check the lid interlock. Every 200 operating hours, clean the water chiller filter. Every 1000 operating hours, grease the honeycomb bed mount with grease GR-1.

## Spare parts {#laser1-parts}

PN-X1Q-991-A: honeycomb bed.
PN-X1Q-991-B: focus lens.
PN-X1Q-199-A: second mirror.
PN-X1Q-199-B: air filter.
PN-X1Q-919-A: nozzle cone.
PN-X1Q-919-B: first mirror.

## Troubleshooting {#laser1-troubleshooting}

The laser tube gets too hot after long runs: the water chiller filter is clogged. Clean it.
The power drifts during a job: sensor S20 needs calibration. Use calibration tool CT-24.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#laser1-safety}

Wear laser safety glasses. Before maintenance, lock out breaker CB-57 and hang your own lock. Two people are needed to replace the focus lens.

## Installation requirements {#laser1-installation}

The Kestrel LX-69 needs a 230 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1300 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 11 and 33 °C, with a relative humidity below 60%.

## Start-up procedure {#laser1-startup}

1. Check that the lid is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the water chiller and wait until the laser tube is below 21 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P652 for a test run, and check the first part before you start a batch.

## Calibration {#laser1-calibration}

Calibrate the Kestrel LX-69 every 1 months, and after any crash or part replacement. Use calibration tool CT-24 and the reference block RB-612. The measured power must be within ±1% of the set value; if it is not, adjust offset parameter K83 and repeat. Write the result in the machine log.
