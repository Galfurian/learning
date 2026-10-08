# Heron M-22 CNC mill (cell 1C)

## Overview {#mill3-overview}

The Heron M-22 is a CNC mill in cell 1C. It was installed in 2023 and runs three shifts a day. Before a run, check that the coolant pump is running and that the door is closed. Service extension: 855.

## Approved materials {#mill3-materials}

Approved materials for the Heron M-22: mild steel, POM and brass. Never process glass-filled plastics: they wear the tools fast. The largest part is 150 × 300 mm.

## Operating settings {#mill3-settings}

The nominal spindle speed of the Heron M-22 is 12000 rpm. The allowed range is 10000–14000 rpm. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the spindle.

## Cooling {#mill3-cooling}

The coolant pump keeps the spindle between 18 and 23 °C. Above 31 °C the machine stops with code E-3320. Check the coolant pump every 14 days.

## Error codes {#mill3-errors}

E-3023: the coolant pump is not running. Check its fuse F7 and its connector.
E-3032: drive overcurrent on axis Y. Remove any jam, then restart.
E-3203: the door interlock opened during a run. Close the door and press RESET.
E-3230: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-3302: sensor S24 does not respond. Check its cable at terminal X5.
E-3320: the spindle is above its limit of 75 °C. Let it cool for 30 minutes before a restart.

## Maintenance schedule {#mill3-maintenance}

Every day, check the door interlock. Every 250 operating hours, clean the coolant pump filter. Every 1500 operating hours, grease the coolant nozzle mount with grease GR-2.

## Spare parts {#mill3-parts}

PN-X3U-199-A: coolant nozzle.
PN-X3U-199-B: spindle belt.
PN-X3U-919-A: tool holder.
PN-X3U-919-B: chip auger.
PN-X3U-991-A: probe stylus.
PN-X3U-991-B: way cover.

## Troubleshooting {#mill3-troubleshooting}

The spindle gets too hot after long runs: the coolant pump filter is clogged. Clean it.
The spindle speed drifts during a job: sensor S24 needs calibration. Use calibration tool CT-94.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#mill3-safety}

Wear safety glasses. Before maintenance, lock out breaker CB-41 and hang your own lock. Two people are needed to replace the spindle belt.

## Installation requirements {#mill3-installation}

The Heron M-22 needs a 230 V supply protected by a 20 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 1200 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 10 and 33 °C, with a relative humidity below 60%.

## Start-up procedure {#mill3-startup}

1. Check that the door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the coolant pump and wait until the spindle is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P719 for a test run, and check the first part before you start a batch.

## Calibration {#mill3-calibration}

Calibrate the Heron M-22 every 2 months, and after any crash or part replacement. Use calibration tool CT-94 and the reference block RB-411. The measured spindle speed must be within ±1% of the set value; if it is not, adjust offset parameter K53 and repeat. Write the result in the machine log.
