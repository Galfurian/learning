# Lynx V-43 vision inspection station (cell 8D)

## Overview {#vision4-overview}

The Lynx V-43 is a vision inspection station in cell 8D. It was installed in 2022 and runs three shifts a day. Before a run, check that the light bar fan is running and that the light shield is closed. Service extension: 807.

## Approved materials {#vision4-materials}

Approved materials for the Lynx V-43: printed labels, painted parts and machined parts. Never process transparent parts: their edges are not visible. The largest part is 100 × 150 mm.

## Operating settings {#vision4-settings}

The nominal exposure time of the Lynx V-43 is 7 ms. The allowed range is 5–9 ms. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the camera.

## Cooling {#vision4-cooling}

The light bar fan keeps the camera between 14 and 19 °C. Above 23 °C the machine stops with code E-8310. Check the light bar fan every 14 days.

## Error codes {#vision4-errors}

E-8013: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-8031: the light bar fan is not running. Check its fuse F8 and its connector.
E-8103: the light shield interlock opened during a run. Close the light shield and press RESET.
E-8130: sensor S42 does not respond. Check its cable at terminal X18.
E-8301: drive overcurrent on axis Y. Remove any jam, then restart.
E-8310: the camera is above its limit of 64 °C. Let it cool for 30 minutes before a restart.

## Maintenance schedule {#vision4-maintenance}

Every day, check the light shield interlock. Every 250 operating hours, clean the light bar fan filter. Every 1500 operating hours, grease the trigger sensor mount with grease GR-3.

## Spare parts {#vision4-parts}

PN-X4W-919-A: trigger sensor.
PN-X4W-919-B: lens cover.
PN-X4W-199-A: ring light.
PN-X4W-199-B: light bar.
PN-X4W-991-A: camera lens.
PN-X4W-991-B: calibration target.

## Troubleshooting {#vision4-troubleshooting}

The camera gets too hot after long runs: the light bar fan filter is clogged. Clean it.
The exposure time drifts during a job: sensor S42 needs calibration. Use calibration tool CT-83.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#vision4-safety}

Wear no special equipment. Before maintenance, lock out breaker CB-43 and hang your own lock. Two people are needed to replace the lens cover.

## Installation requirements {#vision4-installation}

The Lynx V-43 needs a 400 V supply protected by a 20 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 500 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 15 and 32 °C, with a relative humidity below 80%.

## Start-up procedure {#vision4-startup}

1. Check that the light shield is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the light bar fan and wait until the camera is below 19 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P606 for a test run, and check the first part before you start a batch.

## Calibration {#vision4-calibration}

Calibrate the Lynx V-43 every 2 months, and after any crash or part replacement. Use calibration tool CT-83 and the reference block RB-235. The measured exposure time must be within ±3% of the set value; if it is not, adjust offset parameter K83 and repeat. Write the result in the machine log.
