# Lynx V-79 vision inspection station (cell 5C)

## Overview {#vision3-overview}

The Lynx V-79 is a vision inspection station in cell 5C. It was installed in 2018 and runs three shifts a day. Before a run, check that the light bar fan is running and that the light shield is closed. Service extension: 809.

## Approved materials {#vision3-materials}

Approved materials for the Lynx V-79: machined parts, painted parts and printed labels. Never process mirror-polished parts: the reflections blind the camera. The largest part is 250 × 250 mm.

## Operating settings {#vision3-settings}

The nominal exposure time of the Lynx V-79 is 4 ms. The allowed range is 2–6 ms. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the camera.

## Cooling {#vision3-cooling}

The light bar fan keeps the camera between 15 and 22 °C. Above 28 °C the machine stops with code E-8302. Check the light bar fan every 14 days.

## Error codes {#vision3-errors}

E-8023: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-8032: the light shield interlock opened during a run. Close the light shield and press RESET.
E-8203: drive overcurrent on axis Z. Remove any jam, then restart.
E-8230: sensor S49 does not respond. Check its cable at terminal X11.
E-8302: the camera is above its limit of 83 °C. Let it cool for 20 minutes before a restart.
E-8320: the light bar fan is not running. Check its fuse F1 and its connector.

## Maintenance schedule {#vision3-maintenance}

Every day, check the light shield interlock. Every 200 operating hours, clean the light bar fan filter. Every 1500 operating hours, grease the calibration target mount with grease GR-5.

## Spare parts {#vision3-parts}

PN-X3W-991-A: calibration target.
PN-X3W-991-B: lens cover.
PN-X3W-919-A: light bar.
PN-X3W-919-B: ring light.
PN-X3W-199-A: camera lens.
PN-X3W-199-B: trigger sensor.

## Troubleshooting {#vision3-troubleshooting}

The camera gets too hot after long runs: the light bar fan filter is clogged. Clean it.
The exposure time drifts during a job: sensor S49 needs calibration. Use calibration tool CT-94.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#vision3-safety}

Wear no special equipment. Before maintenance, lock out breaker CB-42 and hang your own lock. Two people are needed to replace the lens cover.

## Installation requirements {#vision3-installation}

The Lynx V-79 needs a 230 V supply protected by a 25 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 900 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 14 and 28 °C, with a relative humidity below 80%.

## Start-up procedure {#vision3-startup}

1. Check that the light shield is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the light bar fan and wait until the camera is below 22 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P599 for a test run, and check the first part before you start a batch.

## Calibration {#vision3-calibration}

Calibrate the Lynx V-79 every 6 months, and after any crash or part replacement. Use calibration tool CT-94 and the reference block RB-991. The measured exposure time must be within ±1% of the set value; if it is not, adjust offset parameter K63 and repeat. Write the result in the machine log.
