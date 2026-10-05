# Heron M-58 CNC mill (cell 1D)

## Overview {#mill4-overview}

The Heron M-58 is a CNC mill in cell 1D. It was installed in 2025 and runs one shifts a day. Before a run, check that the coolant pump is running and that the door is closed. Service extension: 699.

## Approved materials {#mill4-materials}

Approved materials for the Heron M-58: brass, POM and mild steel. Never process glass-filled plastics: they wear the tools fast. The largest part is 350 × 200 mm.

## Operating settings {#mill4-settings}

The nominal spindle speed of the Heron M-58 is 18000 rpm. The allowed range is 16000–20000 rpm. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the spindle.

## Cooling {#mill4-cooling}

The coolant pump keeps the spindle between 15 and 20 °C. Above 23 °C the machine stops with code E-3301. Check the coolant pump every 14 days.

## Error codes {#mill4-errors}

E-3013: drive overcurrent on axis Z. Remove any jam, then restart.
E-3031: sensor S44 does not respond. Check its cable at terminal X15.
E-3103: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-3130: the coolant pump is not running. Check its fuse F6 and its connector.
E-3301: the spindle is above its limit of 77 °C. Let it cool for 10 minutes before a restart.
E-3310: the door interlock opened during a run. Close the door and press RESET.

## Maintenance schedule {#mill4-maintenance}

Every day, check the door interlock. Every 100 operating hours, clean the coolant pump filter. Every 1000 operating hours, grease the way cover mount with grease GR-2.

## Spare parts {#mill4-parts}

PN-X4U-919-A: way cover.
PN-X4U-919-B: chip auger.
PN-X4U-199-A: spindle belt.
PN-X4U-199-B: tool holder.
PN-X4U-991-A: coolant nozzle.
PN-X4U-991-B: probe stylus.

## Troubleshooting {#mill4-troubleshooting}

The spindle gets too hot after long runs: the coolant pump filter is clogged. Clean it.
The spindle speed drifts during a job: sensor S44 needs calibration. Use calibration tool CT-24.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#mill4-safety}

Wear safety glasses. Before maintenance, lock out breaker CB-29 and hang your own lock. Two people are needed to replace the chip auger.

## Installation requirements {#mill4-installation}

The Heron M-58 needs a 230 V supply protected by a 25 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1300 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 10 and 31 °C, with a relative humidity below 60%.

## Start-up procedure {#mill4-startup}

1. Check that the door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the coolant pump and wait until the spindle is below 20 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P789 for a test run, and check the first part before you start a batch.

## Calibration {#mill4-calibration}

Calibrate the Heron M-58 every 1 months, and after any crash or part replacement. Use calibration tool CT-24 and the reference block RB-999. The measured spindle speed must be within ±5% of the set value; if it is not, adjust offset parameter K75 and repeat. Write the result in the machine log.
