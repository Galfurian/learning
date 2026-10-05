# Marten S-90 packaging sealer (cell 3D)

## Overview {#sealer4-overview}

The Marten S-90 is a packaging sealer in cell 3D. It was installed in 2021 and runs three shifts a day. Before a run, check that the jaw cooling air is running and that the front guard is closed. Service extension: 738.

## Approved materials {#sealer4-materials}

Approved materials for the Marten S-90: PE film, PP film and laminated film. Never process foil laminates without a sealant layer: they do not seal. The largest part is 200 × 250 mm.

## Operating settings {#sealer4-settings}

The nominal jaw temperature of the Marten S-90 is 140 °C. The allowed range is 125–155 °C. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the sealing jaw.

## Cooling {#sealer4-cooling}

The jaw cooling air keeps the sealing jaw between 16 and 25 °C. Above 31 °C the machine stops with code E-9301. Check the jaw cooling air every 7 days.

## Error codes {#sealer4-errors}

E-9013: drive overcurrent on axis Z. Remove any jam, then restart.
E-9031: the jaw cooling air is not running. Check its fuse F6 and its connector.
E-9103: sensor S49 does not respond. Check its cable at terminal X19.
E-9130: the air pressure is below 2.5 bar. Check the supply hose and the inline filter.
E-9301: the sealing jaw is above its limit of 70 °C. Let it cool for 20 minutes before a restart.
E-9310: the front guard interlock opened during a run. Close the front guard and press RESET.

## Maintenance schedule {#sealer4-maintenance}

Every day, check the front guard interlock. Every 100 operating hours, clean the jaw cooling air filter. Every 500 operating hours, grease the pressure spring mount with grease GR-2.

## Spare parts {#sealer4-parts}

PN-X4Y-199-A: pressure spring.
PN-X4Y-199-B: film knife.
PN-X4Y-919-A: heater element.
PN-X4Y-919-B: sealing jaw.
PN-X4Y-991-A: Teflon tape.
PN-X4Y-991-B: film roller.

## Troubleshooting {#sealer4-troubleshooting}

The sealing jaw gets too hot after long runs: the jaw cooling air filter is clogged. Clean it.
The jaw temperature drifts during a job: sensor S49 needs calibration. Use calibration tool CT-78.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#sealer4-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-17 and hang your own lock. Two people are needed to replace the film knife.

## Installation requirements {#sealer4-installation}

The Marten S-90 needs a 400 V supply protected by a 20 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 500 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 11 and 29 °C, with a relative humidity below 60%.

## Start-up procedure {#sealer4-startup}

1. Check that the front guard is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 20 s for the controller to boot.
3. Start the jaw cooling air and wait until the sealing jaw is below 25 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P488 for a test run, and check the first part before you start a batch.

## Calibration {#sealer4-calibration}

Calibrate the Marten S-90 every 2 months, and after any crash or part replacement. Use calibration tool CT-78 and the reference block RB-615. The measured jaw temperature must be within ±3% of the set value; if it is not, adjust offset parameter K18 and repeat. Write the result in the machine log.
