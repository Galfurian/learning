# Corvid RF-31 reflow oven (cell 1B)

## Overview {#oven2-overview}

The Corvid RF-31 is a reflow oven in cell 1B. It was installed in 2024 and runs one shifts a day. Before a run, check that the cooling fan is running and that the hood is closed. Service extension: 414.

## Approved materials {#oven2-materials}

Approved materials for the Corvid RF-31: aluminium core boards, FR-4 boards and polyimide flex boards. Never process paper-based boards: they char. The largest part is 200 × 100 mm.

## Operating settings {#oven2-settings}

The nominal peak temperature of the Corvid RF-31 is 245 °C. The allowed range is 235–255 °C. Change it only between jobs. At the upper limit, lower the feed by 10% to protect the heater bank.

## Cooling {#oven2-cooling}

The cooling fan keeps the heater bank between 18 and 26 °C. Above 29 °C the machine stops with code E-7132. Check the cooling fan every 3 days.

## Error codes {#oven2-errors}

E-7123: sensor S30 does not respond. Check its cable at terminal X23.
E-7132: the heater bank is above its limit of 81 °C. Let it cool for 30 minutes before a restart.
E-7213: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-7231: the hood interlock opened during a run. Close the hood and press RESET.
E-7312: drive overcurrent on axis X. Remove any jam, then restart.
E-7321: the cooling fan is not running. Check its fuse F6 and its connector.

## Maintenance schedule {#oven2-maintenance}

Every day, check the hood interlock. Every 250 operating hours, clean the cooling fan filter. Every 1500 operating hours, grease the zone heater mount with grease GR-3.

## Spare parts {#oven2-parts}

PN-X2S-199-A: zone heater.
PN-X2S-199-B: door seal.
PN-X2S-919-A: conveyor mesh.
PN-X2S-919-B: thermocouple.
PN-X2S-991-A: exhaust damper.
PN-X2S-991-B: convection fan motor.

## Troubleshooting {#oven2-troubleshooting}

The heater bank gets too hot after long runs: the cooling fan filter is clogged. Clean it.
The peak temperature drifts during a job: sensor S30 needs calibration. Use calibration tool CT-22.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 10-minute warm-up before the first job.

## Safety {#oven2-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-28 and hang your own lock. Two people are needed to replace the door seal.

## Installation requirements {#oven2-installation}

The Corvid RF-31 needs a 230 V supply protected by a 32 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 600 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 10 and 32 °C, with a relative humidity below 60%.

## Start-up procedure {#oven2-startup}

1. Check that the hood is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the cooling fan and wait until the heater bank is below 26 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P356 for a test run, and check the first part before you start a batch.

## Calibration {#oven2-calibration}

Calibrate the Corvid RF-31 every 3 months, and after any crash or part replacement. Use calibration tool CT-22 and the reference block RB-366. The measured peak temperature must be within ±2% of the set value; if it is not, adjust offset parameter K35 and repeat. Write the result in the machine log.
