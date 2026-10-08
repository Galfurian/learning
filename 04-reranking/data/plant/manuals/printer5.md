# Bramble P-48 3D printer (cell 6E)

## Overview {#printer5-overview}

The Bramble P-48 is a 3D printer in cell 6E. It was installed in 2021 and runs three shifts a day. Before a run, check that the hotend fan is running and that the enclosure door is closed. Service extension: 896.

## Approved materials {#printer5-materials}

Approved materials for the Bramble P-48: TPU, ASA and nylon. Never process carbon-filled filament: it wears the brass nozzle. The largest part is 250 × 250 mm.

## Operating settings {#printer5-settings}

The nominal nozzle temperature of the Bramble P-48 is 240 °C. The allowed range is 225–255 °C. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the hotend.

## Cooling {#printer5-cooling}

The hotend fan keeps the hotend between 20 and 25 °C. Above 30 °C the machine stops with code E-2412. Check the hotend fan every 14 days.

## Error codes {#printer5-errors}

E-2124: the enclosure door interlock opened during a run. Close the enclosure door and press RESET.
E-2142: drive overcurrent on axis Y. Remove any jam, then restart.
E-2214: sensor S22 does not respond. Check its cable at terminal X21.
E-2241: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-2412: the hotend is above its limit of 92 °C. Let it cool for 30 minutes before a restart.
E-2421: the hotend fan is not running. Check its fuse F3 and its connector.

## Maintenance schedule {#printer5-maintenance}

Every day, check the enclosure door interlock. Every 100 operating hours, clean the hotend fan filter. Every 500 operating hours, grease the heater cartridge mount with grease GR-3.

## Spare parts {#printer5-parts}

PN-X5R-199-A: heater cartridge.
PN-X5R-199-B: extruder gear.
PN-X5R-919-A: thermistor.
PN-X5R-919-B: Z lead screw.
PN-X5R-991-A: build sheet.
PN-X5R-991-B: nozzle.

## Troubleshooting {#printer5-troubleshooting}

The hotend gets too hot after long runs: the hotend fan filter is clogged. Clean it.
The nozzle temperature drifts during a job: sensor S22 needs calibration. Use calibration tool CT-75.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#printer5-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-42 and hang your own lock. Two people are needed to replace the extruder gear.

## Installation requirements {#printer5-installation}

The Bramble P-48 needs a 230 V supply protected by a 16 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 500 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 13 and 35 °C, with a relative humidity below 60%.

## Start-up procedure {#printer5-startup}

1. Check that the enclosure door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the hotend fan and wait until the hotend is below 25 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P180 for a test run, and check the first part before you start a batch.

## Calibration {#printer5-calibration}

Calibrate the Bramble P-48 every 6 months, and after any crash or part replacement. Use calibration tool CT-75 and the reference block RB-365. The measured nozzle temperature must be within ±2% of the set value; if it is not, adjust offset parameter K84 and repeat. Write the result in the machine log.
