# Lynx V-56 vision inspection station (cell 4A)

## Overview {#vision1-overview}

The Lynx V-56 is a vision inspection station in cell 4A. It was installed in 2020 and runs two shifts a day. Before a run, check that the light bar fan is running and that the light shield is closed. Service extension: 271.

## Approved materials {#vision1-materials}

Approved materials for the Lynx V-56: machined parts, painted parts and printed labels. Never process transparent parts: their edges are not visible. The largest part is 100 × 300 mm.

## Operating settings {#vision1-settings}

The nominal exposure time of the Lynx V-56 is 11 ms. The allowed range is 9–13 ms. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the camera.

## Cooling {#vision1-cooling}

The light bar fan keeps the camera between 19 and 28 °C. Above 36 °C the machine stops with code E-8102. Check the light bar fan every 5 days.

## Error codes {#vision1-errors}

E-8012: drive overcurrent on axis Y. Remove any jam, then restart.
E-8021: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-8102: the camera is above its limit of 85 °C. Let it cool for 10 minutes before a restart.
E-8120: the light bar fan is not running. Check its fuse F9 and its connector.
E-8201: sensor S35 does not respond. Check its cable at terminal X11.
E-8210: the light shield interlock opened during a run. Close the light shield and press RESET.

## Maintenance schedule {#vision1-maintenance}

Every day, check the light shield interlock. Every 250 operating hours, clean the light bar fan filter. Every 500 operating hours, grease the calibration target mount with grease GR-3.

## Spare parts {#vision1-parts}

PN-X1W-919-A: calibration target.
PN-X1W-919-B: light bar.
PN-X1W-991-A: ring light.
PN-X1W-991-B: lens cover.
PN-X1W-199-A: camera lens.
PN-X1W-199-B: trigger sensor.

## Troubleshooting {#vision1-troubleshooting}

The camera gets too hot after long runs: the light bar fan filter is clogged. Clean it.
The exposure time drifts during a job: sensor S35 needs calibration. Use calibration tool CT-96.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#vision1-safety}

Wear no special equipment. Before maintenance, lock out breaker CB-33 and hang your own lock. Two people are needed to replace the light bar.

## Installation requirements {#vision1-installation}

The Lynx V-56 needs a 400 V supply protected by a 25 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 1200 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 13 and 28 °C, with a relative humidity below 70%.

## Start-up procedure {#vision1-startup}

1. Check that the light shield is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the light bar fan and wait until the camera is below 28 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P933 for a test run, and check the first part before you start a batch.

## Calibration {#vision1-calibration}

Calibrate the Lynx V-56 every 6 months, and after any crash or part replacement. Use calibration tool CT-96 and the reference block RB-919. The measured exposure time must be within ±5% of the set value; if it is not, adjust offset parameter K37 and repeat. Write the result in the machine log.
