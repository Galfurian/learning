# Corvid RF-87 reflow oven (cell 4C)

## Overview {#oven3-overview}

The Corvid RF-87 is a reflow oven in cell 4C. It was installed in 2017 and runs one shifts a day. Before a run, check that the cooling fan is running and that the hood is closed. Service extension: 571.

## Approved materials {#oven3-materials}

Approved materials for the Corvid RF-87: FR-4 boards, aluminium core boards and polyimide flex boards. Never process paper-based boards: they char. The largest part is 450 × 200 mm.

## Operating settings {#oven3-settings}

The nominal peak temperature of the Corvid RF-87 is 250 °C. The allowed range is 240–260 °C. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the heater bank.

## Cooling {#oven3-cooling}

The cooling fan keeps the heater bank between 18 and 27 °C. Above 35 °C the machine stops with code E-7203. Check the cooling fan every 14 days.

## Error codes {#oven3-errors}

E-7023: the cooling fan is not running. Check its fuse F2 and its connector.
E-7032: drive overcurrent on axis X. Remove any jam, then restart.
E-7203: the heater bank is above its limit of 76 °C. Let it cool for 20 minutes before a restart.
E-7230: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-7302: the hood interlock opened during a run. Close the hood and press RESET.
E-7320: sensor S21 does not respond. Check its cable at terminal X1.

## Maintenance schedule {#oven3-maintenance}

Every day, check the hood interlock. Every 100 operating hours, clean the cooling fan filter. Every 500 operating hours, grease the door seal mount with grease GR-5.

## Spare parts {#oven3-parts}

PN-X3S-919-A: door seal.
PN-X3S-919-B: zone heater.
PN-X3S-199-A: conveyor mesh.
PN-X3S-199-B: thermocouple.
PN-X3S-991-A: convection fan motor.
PN-X3S-991-B: exhaust damper.

## Troubleshooting {#oven3-troubleshooting}

The heater bank gets too hot after long runs: the cooling fan filter is clogged. Clean it.
The peak temperature drifts during a job: sensor S21 needs calibration. Use calibration tool CT-27.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#oven3-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-50 and hang your own lock. Two people are needed to replace the zone heater.

## Installation requirements {#oven3-installation}

The Corvid RF-87 needs a 400 V supply protected by a 25 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1300 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 11 and 33 °C, with a relative humidity below 60%.

## Start-up procedure {#oven3-startup}

1. Check that the hood is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the cooling fan and wait until the heater bank is below 27 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P373 for a test run, and check the first part before you start a batch.

## Calibration {#oven3-calibration}

Calibrate the Corvid RF-87 every 2 months, and after any crash or part replacement. Use calibration tool CT-27 and the reference block RB-514. The measured peak temperature must be within ±1% of the set value; if it is not, adjust offset parameter K13 and repeat. Write the result in the machine log.
