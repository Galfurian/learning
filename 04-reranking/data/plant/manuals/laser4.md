# Kestrel LX-44 laser cutter (cell 4D)

## Overview {#laser4-overview}

The Kestrel LX-44 is a laser cutter in cell 4D. It was installed in 2019 and runs two shifts a day. Before a run, check that the water chiller is running and that the lid is closed. Service extension: 436.

## Approved materials {#laser4-materials}

Approved materials for the Kestrel LX-44: felt, acrylic and birch plywood. Never process PVC: it releases chlorine gas. The largest part is 350 × 300 mm.

## Operating settings {#laser4-settings}

The nominal power of the Kestrel LX-44 is 60 %. The allowed range is 45–75 %. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the laser tube.

## Cooling {#laser4-cooling}

The water chiller keeps the laser tube between 15 and 21 °C. Above 25 °C the machine stops with code E-4301. Check the water chiller every 3 days.

## Error codes {#laser4-errors}

E-4013: drive overcurrent on axis Z. Remove any jam, then restart.
E-4031: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-4103: sensor S11 does not respond. Check its cable at terminal X19.
E-4130: the lid interlock opened during a run. Close the lid and press RESET.
E-4301: the laser tube is above its limit of 94 °C. Let it cool for 10 minutes before a restart.
E-4310: the water chiller is not running. Check its fuse F5 and its connector.

## Maintenance schedule {#laser4-maintenance}

Every day, check the lid interlock. Every 100 operating hours, clean the water chiller filter. Every 1000 operating hours, grease the focus lens mount with grease GR-5.

## Spare parts {#laser4-parts}

PN-X4Q-919-A: focus lens.
PN-X4Q-919-B: first mirror.
PN-X4Q-991-A: air filter.
PN-X4Q-991-B: honeycomb bed.
PN-X4Q-199-A: second mirror.
PN-X4Q-199-B: nozzle cone.

## Troubleshooting {#laser4-troubleshooting}

The laser tube gets too hot after long runs: the water chiller filter is clogged. Clean it.
The power drifts during a job: sensor S11 needs calibration. Use calibration tool CT-79.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#laser4-safety}

Wear laser safety glasses. Before maintenance, lock out breaker CB-49 and hang your own lock. Two people are needed to replace the first mirror.

## Installation requirements {#laser4-installation}

The Kestrel LX-44 needs a 230 V supply protected by a 32 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 1300 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 10 and 31 °C, with a relative humidity below 60%.

## Start-up procedure {#laser4-startup}

1. Check that the lid is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the water chiller and wait until the laser tube is below 21 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P166 for a test run, and check the first part before you start a batch.

## Calibration {#laser4-calibration}

Calibrate the Kestrel LX-44 every 1 months, and after any crash or part replacement. Use calibration tool CT-79 and the reference block RB-463. The measured power must be within ±5% of the set value; if it is not, adjust offset parameter K80 and repeat. Write the result in the machine log.
