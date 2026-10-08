# Bramble P-33 3D printer (cell 2A)

## Overview {#printer1-overview}

The Bramble P-33 is a 3D printer in cell 2A. It was installed in 2021 and runs three shifts a day. Before a run, check that the hotend fan is running and that the enclosure door is closed. Service extension: 340.

## Approved materials {#printer1-materials}

Approved materials for the Bramble P-33: PLA, PETG and ASA. Never process PEEK: the hotend cannot reach its temperature. The largest part is 150 × 200 mm.

## Operating settings {#printer1-settings}

The nominal nozzle temperature of the Bramble P-33 is 200 °C. The allowed range is 185–215 °C. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the hotend.

## Cooling {#printer1-cooling}

The hotend fan keeps the hotend between 16 and 24 °C. Above 31 °C the machine stops with code E-2102. Check the hotend fan every 14 days.

## Error codes {#printer1-errors}

E-2012: the hotend fan is not running. Check its fuse F7 and its connector.
E-2021: drive overcurrent on axis Y. Remove any jam, then restart.
E-2102: the hotend is above its limit of 73 °C. Let it cool for 10 minutes before a restart.
E-2120: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-2201: sensor S29 does not respond. Check its cable at terminal X15.
E-2210: the enclosure door interlock opened during a run. Close the enclosure door and press RESET.

## Maintenance schedule {#printer1-maintenance}

Every day, check the enclosure door interlock. Every 150 operating hours, clean the hotend fan filter. Every 750 operating hours, grease the build sheet mount with grease GR-2.

## Spare parts {#printer1-parts}

PN-X1R-199-A: build sheet.
PN-X1R-199-B: heater cartridge.
PN-X1R-919-A: thermistor.
PN-X1R-919-B: extruder gear.
PN-X1R-991-A: nozzle.
PN-X1R-991-B: Z lead screw.

## Troubleshooting {#printer1-troubleshooting}

The hotend gets too hot after long runs: the hotend fan filter is clogged. Clean it.
The nozzle temperature drifts during a job: sensor S29 needs calibration. Use calibration tool CT-88.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#printer1-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-59 and hang your own lock. Two people are needed to replace the heater cartridge.

## Installation requirements {#printer1-installation}

The Bramble P-33 needs a 400 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1400 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 13 and 31 °C, with a relative humidity below 80%.

## Start-up procedure {#printer1-startup}

1. Check that the enclosure door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the hotend fan and wait until the hotend is below 24 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P614 for a test run, and check the first part before you start a batch.

## Calibration {#printer1-calibration}

Calibrate the Bramble P-33 every 1 months, and after any crash or part replacement. Use calibration tool CT-88 and the reference block RB-574. The measured nozzle temperature must be within ±1% of the set value; if it is not, adjust offset parameter K46 and repeat. Write the result in the machine log.
