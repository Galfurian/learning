# Heron M-13 CNC mill (cell 7E)

## Overview {#mill5-overview}

The Heron M-13 is a CNC mill in cell 7E. It was installed in 2023 and runs three shifts a day. Before a run, check that the coolant pump is running and that the door is closed. Service extension: 799.

## Approved materials {#mill5-materials}

Approved materials for the Heron M-13: brass, aluminium and mild steel. Never process glass-filled plastics: they wear the tools fast. The largest part is 100 × 300 mm.

## Operating settings {#mill5-settings}

The nominal spindle speed of the Heron M-13 is 12000 rpm. The allowed range is 10000–14000 rpm. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the spindle.

## Cooling {#mill5-cooling}

The coolant pump keeps the spindle between 18 and 23 °C. Above 29 °C the machine stops with code E-3241. Check the coolant pump every 5 days.

## Error codes {#mill5-errors}

E-3124: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-3142: the coolant pump is not running. Check its fuse F9 and its connector.
E-3214: drive overcurrent on axis Z. Remove any jam, then restart.
E-3241: the spindle is above its limit of 79 °C. Let it cool for 30 minutes before a restart.
E-3412: the door interlock opened during a run. Close the door and press RESET.
E-3421: sensor S16 does not respond. Check its cable at terminal X22.

## Maintenance schedule {#mill5-maintenance}

Every day, check the door interlock. Every 250 operating hours, clean the coolant pump filter. Every 1500 operating hours, grease the probe stylus mount with grease GR-2.

## Spare parts {#mill5-parts}

PN-X5U-991-A: probe stylus.
PN-X5U-991-B: coolant nozzle.
PN-X5U-919-A: chip auger.
PN-X5U-919-B: way cover.
PN-X5U-199-A: tool holder.
PN-X5U-199-B: spindle belt.

## Troubleshooting {#mill5-troubleshooting}

The spindle gets too hot after long runs: the coolant pump filter is clogged. Clean it.
The spindle speed drifts during a job: sensor S16 needs calibration. Use calibration tool CT-96.
The machine stops without an error code: the emergency stop on the right panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#mill5-safety}

Wear safety glasses. Before maintenance, lock out breaker CB-42 and hang your own lock. Two people are needed to replace the coolant nozzle.

## Installation requirements {#mill5-installation}

The Heron M-13 needs a 230 V supply protected by a 16 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 400 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 13 and 31 °C, with a relative humidity below 80%.

## Start-up procedure {#mill5-startup}

1. Check that the door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the coolant pump and wait until the spindle is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P848 for a test run, and check the first part before you start a batch.

## Calibration {#mill5-calibration}

Calibrate the Heron M-13 every 3 months, and after any crash or part replacement. Use calibration tool CT-96 and the reference block RB-418. The measured spindle speed must be within ±2% of the set value; if it is not, adjust offset parameter K14 and repeat. Write the result in the machine log.
