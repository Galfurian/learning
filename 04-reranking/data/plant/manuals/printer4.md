# Bramble P-10 3D printer (cell 9D)

## Overview {#printer4-overview}

The Bramble P-10 is a 3D printer in cell 9D. It was installed in 2017 and runs two shifts a day. Before a run, check that the hotend fan is running and that the enclosure door is closed. Service extension: 517.

## Approved materials {#printer4-materials}

Approved materials for the Bramble P-10: TPU, PLA and ASA. Never process PEEK: the hotend cannot reach its temperature. The largest part is 300 × 150 mm.

## Operating settings {#printer4-settings}

The nominal nozzle temperature of the Bramble P-10 is 245 °C. The allowed range is 230–260 °C. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the hotend.

## Cooling {#printer4-cooling}

The hotend fan keeps the hotend between 17 and 26 °C. Above 30 °C the machine stops with code E-2310. Check the hotend fan every 14 days.

## Error codes {#printer4-errors}

E-2013: the hotend fan is not running. Check its fuse F7 and its connector.
E-2031: drive overcurrent on axis Z. Remove any jam, then restart.
E-2103: the enclosure door interlock opened during a run. Close the enclosure door and press RESET.
E-2130: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-2301: sensor S49 does not respond. Check its cable at terminal X4.
E-2310: the hotend is above its limit of 90 °C. Let it cool for 15 minutes before a restart.

## Maintenance schedule {#printer4-maintenance}

Every day, check the enclosure door interlock. Every 150 operating hours, clean the hotend fan filter. Every 1500 operating hours, grease the extruder gear mount with grease GR-3.

## Spare parts {#printer4-parts}

PN-X4R-919-A: extruder gear.
PN-X4R-919-B: thermistor.
PN-X4R-199-A: nozzle.
PN-X4R-199-B: build sheet.
PN-X4R-991-A: Z lead screw.
PN-X4R-991-B: heater cartridge.

## Troubleshooting {#printer4-troubleshooting}

The hotend gets too hot after long runs: the hotend fan filter is clogged. Clean it.
The nozzle temperature drifts during a job: sensor S49 needs calibration. Use calibration tool CT-76.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#printer4-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-32 and hang your own lock. Two people are needed to replace the thermistor.

## Installation requirements {#printer4-installation}

The Bramble P-10 needs a 400 V supply protected by a 20 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1400 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 11 and 31 °C, with a relative humidity below 60%.

## Start-up procedure {#printer4-startup}

1. Check that the enclosure door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the hotend fan and wait until the hotend is below 26 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P119 for a test run, and check the first part before you start a batch.

## Calibration {#printer4-calibration}

Calibrate the Bramble P-10 every 3 months, and after any crash or part replacement. Use calibration tool CT-76 and the reference block RB-960. The measured nozzle temperature must be within ±5% of the set value; if it is not, adjust offset parameter K55 and repeat. Write the result in the machine log.
