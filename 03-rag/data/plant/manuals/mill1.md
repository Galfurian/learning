# Heron M-30 CNC mill (cell 7A)

## Overview {#mill1-overview}

The Heron M-30 is a CNC mill in cell 7A. It was installed in 2024 and runs two shifts a day. Before a run, check that the coolant pump is running and that the door is closed. Service extension: 675.

## Approved materials {#mill1-materials}

Approved materials for the Heron M-30: POM, mild steel and brass. Never process glass-filled plastics: they wear the tools fast. The largest part is 250 × 150 mm.

## Operating settings {#mill1-settings}

The nominal spindle speed of the Heron M-30 is 9000 rpm. The allowed range is 7000–11000 rpm. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the spindle.

## Cooling {#mill1-cooling}

The coolant pump keeps the spindle between 18 and 24 °C. Above 27 °C the machine stops with code E-3120. Check the coolant pump every 3 days.

## Error codes {#mill1-errors}

E-3012: the coolant pump is not running. Check its fuse F8 and its connector.
E-3021: sensor S46 does not respond. Check its cable at terminal X10.
E-3102: the door interlock opened during a run. Close the door and press RESET.
E-3120: the spindle is above its limit of 86 °C. Let it cool for 10 minutes before a restart.
E-3201: drive overcurrent on axis X. Remove any jam, then restart.
E-3210: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.

## Maintenance schedule {#mill1-maintenance}

Every day, check the door interlock. Every 200 operating hours, clean the coolant pump filter. Every 750 operating hours, grease the chip auger mount with grease GR-2.

## Spare parts {#mill1-parts}

PN-X1U-199-A: chip auger.
PN-X1U-199-B: tool holder.
PN-X1U-991-A: probe stylus.
PN-X1U-991-B: spindle belt.
PN-X1U-919-A: way cover.
PN-X1U-919-B: coolant nozzle.

## Troubleshooting {#mill1-troubleshooting}

The spindle gets too hot after long runs: the coolant pump filter is clogged. Clean it.
The spindle speed drifts during a job: sensor S46 needs calibration. Use calibration tool CT-85.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#mill1-safety}

Wear safety glasses. Before maintenance, lock out breaker CB-11 and hang your own lock. Two people are needed to replace the tool holder.

## Installation requirements {#mill1-installation}

The Heron M-30 needs a 400 V supply protected by a 20 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 14 and 28 °C, with a relative humidity below 80%.

## Start-up procedure {#mill1-startup}

1. Check that the door is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the coolant pump and wait until the spindle is below 24 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P835 for a test run, and check the first part before you start a batch.

## Calibration {#mill1-calibration}

Calibrate the Heron M-30 every 2 months, and after any crash or part replacement. Use calibration tool CT-85 and the reference block RB-961. The measured spindle speed must be within ±5% of the set value; if it is not, adjust offset parameter K40 and repeat. Write the result in the machine log.
