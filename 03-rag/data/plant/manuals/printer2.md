# Bramble P-55 3D printer (cell 9B)

## Overview {#printer2-overview}

The Bramble P-55 is a 3D printer in cell 9B. It was installed in 2023 and runs three shifts a day. Before a run, check that the hotend fan is running and that the enclosure door is closed. Service extension: 893.

## Approved materials {#printer2-materials}

Approved materials for the Bramble P-55: nylon, PETG and PLA. Never process carbon-filled filament: it wears the brass nozzle. The largest part is 400 × 100 mm.

## Operating settings {#printer2-settings}

The nominal nozzle temperature of the Bramble P-55 is 215 °C. The allowed range is 200–230 °C. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the hotend.

## Cooling {#printer2-cooling}

The hotend fan keeps the hotend between 14 and 20 °C. Above 25 °C the machine stops with code E-2132. Check the hotend fan every 5 days.

## Error codes {#printer2-errors}

E-2123: the enclosure door interlock opened during a run. Close the enclosure door and press RESET.
E-2132: the hotend is above its limit of 66 °C. Let it cool for 30 minutes before a restart.
E-2213: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-2231: drive overcurrent on axis Z. Remove any jam, then restart.
E-2312: sensor S35 does not respond. Check its cable at terminal X13.
E-2321: the hotend fan is not running. Check its fuse F3 and its connector.

## Maintenance schedule {#printer2-maintenance}

Every day, check the enclosure door interlock. Every 100 operating hours, clean the hotend fan filter. Every 1000 operating hours, grease the thermistor mount with grease GR-5.

## Spare parts {#printer2-parts}

PN-X2R-199-A: thermistor.
PN-X2R-199-B: heater cartridge.
PN-X2R-919-A: Z lead screw.
PN-X2R-919-B: extruder gear.
PN-X2R-991-A: nozzle.
PN-X2R-991-B: build sheet.

## Troubleshooting {#printer2-troubleshooting}

The hotend gets too hot after long runs: the hotend fan filter is clogged. Clean it.
The nozzle temperature drifts during a job: sensor S35 needs calibration. Use calibration tool CT-75.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#printer2-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-53 and hang your own lock. Two people are needed to replace the heater cartridge.

## Installation requirements {#printer2-installation}

The Bramble P-55 needs a 230 V supply protected by a 20 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 15 and 28 °C, with a relative humidity below 80%.

## Start-up procedure {#printer2-startup}

1. Check that the enclosure door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the hotend fan and wait until the hotend is below 20 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P126 for a test run, and check the first part before you start a batch.

## Calibration {#printer2-calibration}

Calibrate the Bramble P-55 every 2 months, and after any crash or part replacement. Use calibration tool CT-75 and the reference block RB-650. The measured nozzle temperature must be within ±1% of the set value; if it is not, adjust offset parameter K68 and repeat. Write the result in the machine log.
