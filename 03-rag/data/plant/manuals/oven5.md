# Corvid RF-40 reflow oven (cell 2E)

## Overview {#oven5-overview}

The Corvid RF-40 is a reflow oven in cell 2E. It was installed in 2025 and runs one shifts a day. Before a run, check that the cooling fan is running and that the hood is closed. Service extension: 381.

## Approved materials {#oven5-materials}

Approved materials for the Corvid RF-40: polyimide flex boards, FR-4 boards and aluminium core boards. Never process paper-based boards: they char. The largest part is 100 × 300 mm.

## Operating settings {#oven5-settings}

The nominal peak temperature of the Corvid RF-40 is 248 °C. The allowed range is 238–258 °C. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the heater bank.

## Cooling {#oven5-cooling}

The cooling fan keeps the heater bank between 18 and 24 °C. Above 30 °C the machine stops with code E-7412. Check the cooling fan every 3 days.

## Error codes {#oven5-errors}

E-7124: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-7142: sensor S21 does not respond. Check its cable at terminal X23.
E-7214: the cooling fan is not running. Check its fuse F4 and its connector.
E-7241: the hood interlock opened during a run. Close the hood and press RESET.
E-7412: the heater bank is above its limit of 80 °C. Let it cool for 10 minutes before a restart.
E-7421: drive overcurrent on axis Y. Remove any jam, then restart.

## Maintenance schedule {#oven5-maintenance}

Every day, check the hood interlock. Every 100 operating hours, clean the cooling fan filter. Every 1000 operating hours, grease the exhaust damper mount with grease GR-3.

## Spare parts {#oven5-parts}

PN-X5S-919-A: exhaust damper.
PN-X5S-919-B: convection fan motor.
PN-X5S-991-A: thermocouple.
PN-X5S-991-B: zone heater.
PN-X5S-199-A: door seal.
PN-X5S-199-B: conveyor mesh.

## Troubleshooting {#oven5-troubleshooting}

The heater bank gets too hot after long runs: the cooling fan filter is clogged. Clean it.
The peak temperature drifts during a job: sensor S21 needs calibration. Use calibration tool CT-85.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#oven5-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-18 and hang your own lock. Two people are needed to replace the convection fan motor.

## Installation requirements {#oven5-installation}

The Corvid RF-40 needs a 230 V supply protected by a 20 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 14 and 35 °C, with a relative humidity below 70%.

## Start-up procedure {#oven5-startup}

1. Check that the hood is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the cooling fan and wait until the heater bank is below 24 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P606 for a test run, and check the first part before you start a batch.

## Calibration {#oven5-calibration}

Calibrate the Corvid RF-40 every 2 months, and after any crash or part replacement. Use calibration tool CT-85 and the reference block RB-301. The measured peak temperature must be within ±5% of the set value; if it is not, adjust offset parameter K44 and repeat. Write the result in the machine log.
