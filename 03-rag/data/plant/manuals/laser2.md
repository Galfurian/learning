# Kestrel LX-88 laser cutter (cell 8B)

## Overview {#laser2-overview}

The Kestrel LX-88 is a laser cutter in cell 8B. It was installed in 2019 and runs two shifts a day. Before a run, check that the water chiller is running and that the lid is closed. Service extension: 403.

## Approved materials {#laser2-materials}

Approved materials for the Kestrel LX-88: cork, acrylic and birch plywood. Never process PVC: it releases chlorine gas. The largest part is 100 × 250 mm.

## Operating settings {#laser2-settings}

The nominal power of the Kestrel LX-88 is 84 %. The allowed range is 69–99 %. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the laser tube.

## Cooling {#laser2-cooling}

The water chiller keeps the laser tube between 15 and 23 °C. Above 26 °C the machine stops with code E-4231. Check the water chiller every 14 days.

## Error codes {#laser2-errors}

E-4123: the lid interlock opened during a run. Close the lid and press RESET.
E-4132: drive overcurrent on axis Y. Remove any jam, then restart.
E-4213: the water chiller is not running. Check its fuse F3 and its connector.
E-4231: the laser tube is above its limit of 62 °C. Let it cool for 10 minutes before a restart.
E-4312: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-4321: sensor S45 does not respond. Check its cable at terminal X22.

## Maintenance schedule {#laser2-maintenance}

Every day, check the lid interlock. Every 200 operating hours, clean the water chiller filter. Every 1500 operating hours, grease the honeycomb bed mount with grease GR-1.

## Spare parts {#laser2-parts}

PN-X2Q-199-A: honeycomb bed.
PN-X2Q-199-B: nozzle cone.
PN-X2Q-991-A: first mirror.
PN-X2Q-991-B: focus lens.
PN-X2Q-919-A: second mirror.
PN-X2Q-919-B: air filter.

## Troubleshooting {#laser2-troubleshooting}

The laser tube gets too hot after long runs: the water chiller filter is clogged. Clean it.
The power drifts during a job: sensor S45 needs calibration. Use calibration tool CT-44.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#laser2-safety}

Wear laser safety glasses. Before maintenance, lock out breaker CB-38 and hang your own lock. Two people are needed to replace the nozzle cone.

## Installation requirements {#laser2-installation}

The Kestrel LX-88 needs a 400 V supply protected by a 25 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 800 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 10 and 28 °C, with a relative humidity below 60%.

## Start-up procedure {#laser2-startup}

1. Check that the lid is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the water chiller and wait until the laser tube is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P926 for a test run, and check the first part before you start a batch.

## Calibration {#laser2-calibration}

Calibrate the Kestrel LX-88 every 6 months, and after any crash or part replacement. Use calibration tool CT-44 and the reference block RB-609. The measured power must be within ±3% of the set value; if it is not, adjust offset parameter K41 and repeat. Write the result in the machine log.
