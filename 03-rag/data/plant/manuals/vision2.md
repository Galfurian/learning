# Lynx V-64 vision inspection station (cell 7B)

## Overview {#vision2-overview}

The Lynx V-64 is a vision inspection station in cell 7B. It was installed in 2016 and runs three shifts a day. Before a run, check that the light bar fan is running and that the light shield is closed. Service extension: 493.

## Approved materials {#vision2-materials}

Approved materials for the Lynx V-64: painted parts, machined parts and printed labels. Never process mirror-polished parts: the reflections blind the camera. The largest part is 250 × 250 mm.

## Operating settings {#vision2-settings}

The nominal exposure time of the Lynx V-64 is 10 ms. The allowed range is 8–12 ms. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the camera.

## Cooling {#vision2-cooling}

The light bar fan keeps the camera between 17 and 25 °C. Above 29 °C the machine stops with code E-8123. Check the light bar fan every 14 days.

## Error codes {#vision2-errors}

E-8123: the camera is above its limit of 90 °C. Let it cool for 10 minutes before a restart.
E-8132: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-8213: the light shield interlock opened during a run. Close the light shield and press RESET.
E-8231: the light bar fan is not running. Check its fuse F8 and its connector.
E-8312: drive overcurrent on axis X. Remove any jam, then restart.
E-8321: sensor S18 does not respond. Check its cable at terminal X8.

## Maintenance schedule {#vision2-maintenance}

Every day, check the light shield interlock. Every 250 operating hours, clean the light bar fan filter. Every 500 operating hours, grease the calibration target mount with grease GR-5.

## Spare parts {#vision2-parts}

PN-X2W-919-A: calibration target.
PN-X2W-919-B: lens cover.
PN-X2W-991-A: light bar.
PN-X2W-991-B: trigger sensor.
PN-X2W-199-A: camera lens.
PN-X2W-199-B: ring light.

## Troubleshooting {#vision2-troubleshooting}

The camera gets too hot after long runs: the light bar fan filter is clogged. Clean it.
The exposure time drifts during a job: sensor S18 needs calibration. Use calibration tool CT-39.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#vision2-safety}

Wear no special equipment. Before maintenance, lock out breaker CB-60 and hang your own lock. Two people are needed to replace the lens cover.

## Installation requirements {#vision2-installation}

The Lynx V-64 needs a 400 V supply protected by a 16 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 13 and 31 °C, with a relative humidity below 70%.

## Start-up procedure {#vision2-startup}

1. Check that the light shield is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the light bar fan and wait until the camera is below 25 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P121 for a test run, and check the first part before you start a batch.

## Calibration {#vision2-calibration}

Calibrate the Lynx V-64 every 3 months, and after any crash or part replacement. Use calibration tool CT-39 and the reference block RB-849. The measured exposure time must be within ±3% of the set value; if it is not, adjust offset parameter K24 and repeat. Write the result in the machine log.
