# Lynx V-27 vision inspection station (cell 6E)

## Overview {#vision5-overview}

The Lynx V-27 is a vision inspection station in cell 6E. It was installed in 2023 and runs two shifts a day. Before a run, check that the light bar fan is running and that the light shield is closed. Service extension: 261.

## Approved materials {#vision5-materials}

Approved materials for the Lynx V-27: printed labels, machined parts and painted parts. Never process transparent parts: their edges are not visible. The largest part is 450 × 150 mm.

## Operating settings {#vision5-settings}

The nominal exposure time of the Lynx V-27 is 6 ms. The allowed range is 4–8 ms. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the camera.

## Cooling {#vision5-cooling}

The light bar fan keeps the camera between 15 and 21 °C. Above 25 °C the machine stops with code E-8124. Check the light bar fan every 3 days.

## Error codes {#vision5-errors}

E-8124: the camera is above its limit of 62 °C. Let it cool for 10 minutes before a restart.
E-8142: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-8214: the light shield interlock opened during a run. Close the light shield and press RESET.
E-8241: the light bar fan is not running. Check its fuse F1 and its connector.
E-8412: sensor S30 does not respond. Check its cable at terminal X10.
E-8421: drive overcurrent on axis Z. Remove any jam, then restart.

## Maintenance schedule {#vision5-maintenance}

Every day, check the light shield interlock. Every 200 operating hours, clean the light bar fan filter. Every 750 operating hours, grease the trigger sensor mount with grease GR-5.

## Spare parts {#vision5-parts}

PN-X5W-991-A: trigger sensor.
PN-X5W-991-B: light bar.
PN-X5W-919-A: lens cover.
PN-X5W-919-B: ring light.
PN-X5W-199-A: calibration target.
PN-X5W-199-B: camera lens.

## Troubleshooting {#vision5-troubleshooting}

The camera gets too hot after long runs: the light bar fan filter is clogged. Clean it.
The exposure time drifts during a job: sensor S30 needs calibration. Use calibration tool CT-60.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#vision5-safety}

Wear no special equipment. Before maintenance, lock out breaker CB-36 and hang your own lock. Two people are needed to replace the light bar.

## Installation requirements {#vision5-installation}

The Lynx V-27 needs a 400 V supply protected by a 25 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 800 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 14 and 33 °C, with a relative humidity below 70%.

## Start-up procedure {#vision5-startup}

1. Check that the light shield is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 30 s for the controller to boot.
3. Start the light bar fan and wait until the camera is below 21 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P560 for a test run, and check the first part before you start a batch.

## Calibration {#vision5-calibration}

Calibrate the Lynx V-27 every 6 months, and after any crash or part replacement. Use calibration tool CT-60 and the reference block RB-927. The measured exposure time must be within ±5% of the set value; if it is not, adjust offset parameter K64 and repeat. Write the result in the machine log.
