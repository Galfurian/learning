# Bramble P-61 3D printer (cell 3C)

## Overview {#printer3-overview}

The Bramble P-61 is a 3D printer in cell 3C. It was installed in 2019 and runs one shifts a day. Before a run, check that the hotend fan is running and that the enclosure door is closed. Service extension: 228.

## Approved materials {#printer3-materials}

Approved materials for the Bramble P-61: TPU, PETG and ASA. Never process PEEK: the hotend cannot reach its temperature. The largest part is 100 × 300 mm.

## Operating settings {#printer3-settings}

The nominal nozzle temperature of the Bramble P-61 is 225 °C. The allowed range is 210–240 °C. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the hotend.

## Cooling {#printer3-cooling}

The hotend fan keeps the hotend between 15 and 24 °C. Above 32 °C the machine stops with code E-2230. Check the hotend fan every 7 days.

## Error codes {#printer3-errors}

E-2023: the hotend fan is not running. Check its fuse F1 and its connector.
E-2032: drive overcurrent on axis Z. Remove any jam, then restart.
E-2203: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-2230: the hotend is above its limit of 95 °C. Let it cool for 10 minutes before a restart.
E-2302: the enclosure door interlock opened during a run. Close the enclosure door and press RESET.
E-2320: sensor S32 does not respond. Check its cable at terminal X16.

## Maintenance schedule {#printer3-maintenance}

Every day, check the enclosure door interlock. Every 100 operating hours, clean the hotend fan filter. Every 1000 operating hours, grease the build sheet mount with grease GR-3.

## Spare parts {#printer3-parts}

PN-X3R-919-A: build sheet.
PN-X3R-919-B: heater cartridge.
PN-X3R-199-A: nozzle.
PN-X3R-199-B: Z lead screw.
PN-X3R-991-A: thermistor.
PN-X3R-991-B: extruder gear.

## Troubleshooting {#printer3-troubleshooting}

The hotend gets too hot after long runs: the hotend fan filter is clogged. Clean it.
The nozzle temperature drifts during a job: sensor S32 needs calibration. Use calibration tool CT-17.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#printer3-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-31 and hang your own lock. Two people are needed to replace the heater cartridge.

## Installation requirements {#printer3-installation}

The Bramble P-61 needs a 400 V supply protected by a 32 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 500 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 11 and 35 °C, with a relative humidity below 70%.

## Start-up procedure {#printer3-startup}

1. Check that the enclosure door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the hotend fan and wait until the hotend is below 24 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P277 for a test run, and check the first part before you start a batch.

## Calibration {#printer3-calibration}

Calibrate the Bramble P-61 every 2 months, and after any crash or part replacement. Use calibration tool CT-17 and the reference block RB-688. The measured nozzle temperature must be within ±2% of the set value; if it is not, adjust offset parameter K91 and repeat. Write the result in the machine log.
