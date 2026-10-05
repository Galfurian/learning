# Marten S-40 packaging sealer (cell 2C)

## Overview {#sealer3-overview}

The Marten S-40 is a packaging sealer in cell 2C. It was installed in 2022 and runs three shifts a day. Before a run, check that the jaw cooling air is running and that the front guard is closed. Service extension: 377.

## Approved materials {#sealer3-materials}

Approved materials for the Marten S-40: PE film, laminated film and PP film. Never process foil laminates without a sealant layer: they do not seal. The largest part is 300 × 150 mm.

## Operating settings {#sealer3-settings}

The nominal jaw temperature of the Marten S-40 is 160 °C. The allowed range is 145–175 °C. Change it only between jobs. At the upper limit, lower the feed by 15% to protect the sealing jaw.

## Cooling {#sealer3-cooling}

The jaw cooling air keeps the sealing jaw between 17 and 23 °C. Above 28 °C the machine stops with code E-9230. Check the jaw cooling air every 5 days.

## Error codes {#sealer3-errors}

E-9023: the air pressure is below 1.5 bar. Check the supply hose and the inline filter.
E-9032: the front guard interlock opened during a run. Close the front guard and press RESET.
E-9203: sensor S34 does not respond. Check its cable at terminal X15.
E-9230: the sealing jaw is above its limit of 95 °C. Let it cool for 20 minutes before a restart.
E-9302: the jaw cooling air is not running. Check its fuse F7 and its connector.
E-9320: drive overcurrent on axis Z. Remove any jam, then restart.

## Maintenance schedule {#sealer3-maintenance}

Every day, check the front guard interlock. Every 100 operating hours, clean the jaw cooling air filter. Every 1500 operating hours, grease the pressure spring mount with grease GR-4.

## Spare parts {#sealer3-parts}

PN-X3Y-199-A: pressure spring.
PN-X3Y-199-B: heater element.
PN-X3Y-919-A: sealing jaw.
PN-X3Y-919-B: film roller.
PN-X3Y-991-A: Teflon tape.
PN-X3Y-991-B: film knife.

## Troubleshooting {#sealer3-troubleshooting}

The sealing jaw gets too hot after long runs: the jaw cooling air filter is clogged. Clean it.
The jaw temperature drifts during a job: sensor S34 needs calibration. Use calibration tool CT-86.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#sealer3-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-25 and hang your own lock. Two people are needed to replace the heater element.

## Installation requirements {#sealer3-installation}

The Marten S-40 needs a 230 V supply protected by a 16 A breaker, and compressed air at 7 bar if the air option is fitted. The floor must carry 1500 kg per square metre. Keep 80 cm free on every side for service access. The room must stay between 12 and 28 °C, with a relative humidity below 60%.

## Start-up procedure {#sealer3-startup}

1. Check that the front guard is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the jaw cooling air and wait until the sealing jaw is below 23 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P243 for a test run, and check the first part before you start a batch.

## Calibration {#sealer3-calibration}

Calibrate the Marten S-40 every 1 months, and after any crash or part replacement. Use calibration tool CT-86 and the reference block RB-411. The measured jaw temperature must be within ±2% of the set value; if it is not, adjust offset parameter K48 and repeat. Write the result in the machine log.
