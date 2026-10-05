# Heron M-78 CNC mill (cell 7B)

## Overview {#mill2-overview}

The Heron M-78 is a CNC mill in cell 7B. It was installed in 2023 and runs two shifts a day. Before a run, check that the coolant pump is running and that the door is closed. Service extension: 643.

## Approved materials {#mill2-materials}

Approved materials for the Heron M-78: brass, mild steel and aluminium. Never process glass-filled plastics: they wear the tools fast. The largest part is 350 × 300 mm.

## Operating settings {#mill2-settings}

The nominal spindle speed of the Heron M-78 is 17000 rpm. The allowed range is 15000–19000 rpm. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the spindle.

## Cooling {#mill2-cooling}

The coolant pump keeps the spindle between 20 and 29 °C. Above 37 °C the machine stops with code E-3312. Check the coolant pump every 14 days.

## Error codes {#mill2-errors}

E-3123: the coolant pump is not running. Check its fuse F6 and its connector.
E-3132: sensor S25 does not respond. Check its cable at terminal X5.
E-3213: the door interlock opened during a run. Close the door and press RESET.
E-3231: drive overcurrent on axis X. Remove any jam, then restart.
E-3312: the spindle is above its limit of 88 °C. Let it cool for 10 minutes before a restart.
E-3321: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.

## Maintenance schedule {#mill2-maintenance}

Every day, check the door interlock. Every 100 operating hours, clean the coolant pump filter. Every 1500 operating hours, grease the tool holder mount with grease GR-5.

## Spare parts {#mill2-parts}

PN-X2U-991-A: tool holder.
PN-X2U-991-B: chip auger.
PN-X2U-919-A: way cover.
PN-X2U-919-B: probe stylus.
PN-X2U-199-A: spindle belt.
PN-X2U-199-B: coolant nozzle.

## Troubleshooting {#mill2-troubleshooting}

The spindle gets too hot after long runs: the coolant pump filter is clogged. Clean it.
The spindle speed drifts during a job: sensor S25 needs calibration. Use calibration tool CT-48.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#mill2-safety}

Wear safety glasses. Before maintenance, lock out breaker CB-24 and hang your own lock. Two people are needed to replace the chip auger.

## Installation requirements {#mill2-installation}

The Heron M-78 needs a 400 V supply protected by a 25 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 1000 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 13 and 32 °C, with a relative humidity below 60%.

## Start-up procedure {#mill2-startup}

1. Check that the door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the coolant pump and wait until the spindle is below 29 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P694 for a test run, and check the first part before you start a batch.

## Calibration {#mill2-calibration}

Calibrate the Heron M-78 every 2 months, and after any crash or part replacement. Use calibration tool CT-48 and the reference block RB-688. The measured spindle speed must be within ±3% of the set value; if it is not, adjust offset parameter K55 and repeat. Write the result in the machine log.
