# Marten S-25 packaging sealer (cell 1B)

## Overview {#sealer2-overview}

The Marten S-25 is a packaging sealer in cell 1B. It was installed in 2025 and runs three shifts a day. Before a run, check that the jaw cooling air is running and that the front guard is closed. Service extension: 348.

## Approved materials {#sealer2-materials}

Approved materials for the Marten S-25: PP film, PE film and laminated film. Never process foil laminates without a sealant layer: they do not seal. The largest part is 250 × 250 mm.

## Operating settings {#sealer2-settings}

The nominal jaw temperature of the Marten S-25 is 165 °C. The allowed range is 150–180 °C. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the sealing jaw.

## Cooling {#sealer2-cooling}

The jaw cooling air keeps the sealing jaw between 18 and 24 °C. Above 30 °C the machine stops with code E-9312. Check the jaw cooling air every 5 days.

## Error codes {#sealer2-errors}

E-9123: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.
E-9132: the jaw cooling air is not running. Check its fuse F1 and its connector.
E-9213: drive overcurrent on axis Z. Remove any jam, then restart.
E-9231: sensor S15 does not respond. Check its cable at terminal X1.
E-9312: the sealing jaw is above its limit of 67 °C. Let it cool for 20 minutes before a restart.
E-9321: the front guard interlock opened during a run. Close the front guard and press RESET.

## Maintenance schedule {#sealer2-maintenance}

Every day, check the front guard interlock. Every 100 operating hours, clean the jaw cooling air filter. Every 1500 operating hours, grease the pressure spring mount with grease GR-5.

## Spare parts {#sealer2-parts}

PN-X2Y-991-A: pressure spring.
PN-X2Y-991-B: Teflon tape.
PN-X2Y-919-A: film knife.
PN-X2Y-919-B: sealing jaw.
PN-X2Y-199-A: heater element.
PN-X2Y-199-B: film roller.

## Troubleshooting {#sealer2-troubleshooting}

The sealing jaw gets too hot after long runs: the jaw cooling air filter is clogged. Clean it.
The jaw temperature drifts during a job: sensor S15 needs calibration. Use calibration tool CT-88.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#sealer2-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-43 and hang your own lock. Two people are needed to replace the Teflon tape.

## Installation requirements {#sealer2-installation}

The Marten S-25 needs a 230 V supply protected by a 16 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1100 kg per square metre. Keep 50 cm free on every side for service access. The room must stay between 12 and 35 °C, with a relative humidity below 80%.

## Start-up procedure {#sealer2-startup}

1. Check that the front guard is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 45 s for the controller to boot.
3. Start the jaw cooling air and wait until the sealing jaw is below 24 °C.
4. Run the homing cycle from the operator panel. It takes about 4 minutes.
5. Load program P815 for a test run, and check the first part before you start a batch.

## Calibration {#sealer2-calibration}

Calibrate the Marten S-25 every 6 months, and after any crash or part replacement. Use calibration tool CT-88 and the reference block RB-682. The measured jaw temperature must be within ±3% of the set value; if it is not, adjust offset parameter K76 and repeat. Write the result in the machine log.
