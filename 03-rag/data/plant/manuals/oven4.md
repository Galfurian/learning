# Corvid RF-13 reflow oven (cell 4D)

## Overview {#oven4-overview}

The Corvid RF-13 is a reflow oven in cell 4D. It was installed in 2024 and runs three shifts a day. Before a run, check that the cooling fan is running and that the hood is closed. Service extension: 369.

## Approved materials {#oven4-materials}

Approved materials for the Corvid RF-13: polyimide flex boards, aluminium core boards and FR-4 boards. Never process boards with unsealed batteries: they can vent. The largest part is 350 × 200 mm.

## Operating settings {#oven4-settings}

The nominal peak temperature of the Corvid RF-13 is 239 °C. The allowed range is 229–249 °C. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the heater bank.

## Cooling {#oven4-cooling}

The cooling fan keeps the heater bank between 20 and 25 °C. Above 29 °C the machine stops with code E-7130. Check the cooling fan every 7 days.

## Error codes {#oven4-errors}

E-7013: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-7031: the cooling fan is not running. Check its fuse F7 and its connector.
E-7103: the hood interlock opened during a run. Close the hood and press RESET.
E-7130: the heater bank is above its limit of 77 °C. Let it cool for 30 minutes before a restart.
E-7301: sensor S36 does not respond. Check its cable at terminal X5.
E-7310: drive overcurrent on axis X. Remove any jam, then restart.

## Maintenance schedule {#oven4-maintenance}

Every day, check the hood interlock. Every 150 operating hours, clean the cooling fan filter. Every 1500 operating hours, grease the conveyor mesh mount with grease GR-1.

## Spare parts {#oven4-parts}

PN-X4S-199-A: conveyor mesh.
PN-X4S-199-B: door seal.
PN-X4S-991-A: convection fan motor.
PN-X4S-991-B: zone heater.
PN-X4S-919-A: thermocouple.
PN-X4S-919-B: exhaust damper.

## Troubleshooting {#oven4-troubleshooting}

The heater bank gets too hot after long runs: the cooling fan filter is clogged. Clean it.
The peak temperature drifts during a job: sensor S36 needs calibration. Use calibration tool CT-23.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#oven4-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-15 and hang your own lock. Two people are needed to replace the door seal.

## Installation requirements {#oven4-installation}

The Corvid RF-13 needs a 230 V supply protected by a 16 A breaker, and compressed air at 6 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 15 and 35 °C, with a relative humidity below 60%.

## Start-up procedure {#oven4-startup}

1. Check that the hood is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the cooling fan and wait until the heater bank is below 25 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P845 for a test run, and check the first part before you start a batch.

## Calibration {#oven4-calibration}

Calibrate the Corvid RF-13 every 2 months, and after any crash or part replacement. Use calibration tool CT-23 and the reference block RB-407. The measured peak temperature must be within ±3% of the set value; if it is not, adjust offset parameter K79 and repeat. Write the result in the machine log.
