# Corvid RF-70 reflow oven (cell 5A)

## Overview {#oven1-overview}

The Corvid RF-70 is a reflow oven in cell 5A. It was installed in 2022 and runs three shifts a day. Before a run, check that the cooling fan is running and that the hood is closed. Service extension: 545.

## Approved materials {#oven1-materials}

Approved materials for the Corvid RF-70: polyimide flex boards, aluminium core boards and FR-4 boards. Never process paper-based boards: they char. The largest part is 150 × 250 mm.

## Operating settings {#oven1-settings}

The nominal peak temperature of the Corvid RF-70 is 235 °C. The allowed range is 225–245 °C. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the heater bank.

## Cooling {#oven1-cooling}

The cooling fan keeps the heater bank between 18 and 23 °C. Above 30 °C the machine stops with code E-7210. Check the cooling fan every 5 days.

## Error codes {#oven1-errors}

E-7012: sensor S21 does not respond. Check its cable at terminal X3.
E-7021: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-7102: the hood interlock opened during a run. Close the hood and press RESET.
E-7120: drive overcurrent on axis Z. Remove any jam, then restart.
E-7201: the cooling fan is not running. Check its fuse F7 and its connector.
E-7210: the heater bank is above its limit of 92 °C. Let it cool for 20 minutes before a restart.

## Maintenance schedule {#oven1-maintenance}

Every day, check the hood interlock. Every 100 operating hours, clean the cooling fan filter. Every 500 operating hours, grease the thermocouple mount with grease GR-4.

## Spare parts {#oven1-parts}

PN-X1S-199-A: thermocouple.
PN-X1S-199-B: convection fan motor.
PN-X1S-919-A: conveyor mesh.
PN-X1S-919-B: exhaust damper.
PN-X1S-991-A: door seal.
PN-X1S-991-B: zone heater.

## Troubleshooting {#oven1-troubleshooting}

The heater bank gets too hot after long runs: the cooling fan filter is clogged. Clean it.
The peak temperature drifts during a job: sensor S21 needs calibration. Use calibration tool CT-28.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#oven1-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-44 and hang your own lock. Two people are needed to replace the convection fan motor.

## Installation requirements {#oven1-installation}

The Corvid RF-70 needs a 400 V supply protected by a 16 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1200 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 15 and 32 °C, with a relative humidity below 70%.

## Start-up procedure {#oven1-startup}

1. Check that the hood is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the cooling fan and wait until the heater bank is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P815 for a test run, and check the first part before you start a batch.

## Calibration {#oven1-calibration}

Calibrate the Corvid RF-70 every 3 months, and after any crash or part replacement. Use calibration tool CT-28 and the reference block RB-883. The measured peak temperature must be within ±2% of the set value; if it is not, adjust offset parameter K45 and repeat. Write the result in the machine log.
