# Marten S-74 packaging sealer (cell 5E)

## Overview {#sealer5-overview}

The Marten S-74 is a packaging sealer in cell 5E. It was installed in 2021 and runs one shifts a day. Before a run, check that the jaw cooling air is running and that the front guard is closed. Service extension: 561.

## Approved materials {#sealer5-materials}

Approved materials for the Marten S-74: PP film, laminated film and PE film. Never process PVC film: it releases fumes. The largest part is 250 × 200 mm.

## Operating settings {#sealer5-settings}

The nominal jaw temperature of the Marten S-74 is 160 °C. The allowed range is 145–175 °C. Change it only between jobs. At the upper limit, lower the feed by 25% to protect the sealing jaw.

## Cooling {#sealer5-cooling}

The jaw cooling air keeps the sealing jaw between 14 and 19 °C. Above 26 °C the machine stops with code E-9412. Check the jaw cooling air every 5 days.

## Error codes {#sealer5-errors}

E-9124: the front guard interlock opened during a run. Close the front guard and press RESET.
E-9142: the jaw cooling air is not running. Check its fuse F1 and its connector.
E-9214: drive overcurrent on axis Z. Remove any jam, then restart.
E-9241: sensor S14 does not respond. Check its cable at terminal X9.
E-9412: the sealing jaw is above its limit of 76 °C. Let it cool for 20 minutes before a restart.
E-9421: the air pressure is below 3.0 bar. Check the supply hose and the inline filter.

## Maintenance schedule {#sealer5-maintenance}

Every day, check the front guard interlock. Every 200 operating hours, clean the jaw cooling air filter. Every 750 operating hours, grease the heater element mount with grease GR-5.

## Spare parts {#sealer5-parts}

PN-X5Y-199-A: heater element.
PN-X5Y-199-B: film knife.
PN-X5Y-919-A: Teflon tape.
PN-X5Y-919-B: film roller.
PN-X5Y-991-A: sealing jaw.
PN-X5Y-991-B: pressure spring.

## Troubleshooting {#sealer5-troubleshooting}

The sealing jaw gets too hot after long runs: the jaw cooling air filter is clogged. Clean it.
The jaw temperature drifts during a job: sensor S14 needs calibration. Use calibration tool CT-73.
The machine stops without an error code: the emergency stop on the rear panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 5-minute warm-up before the first job.

## Safety {#sealer5-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-16 and hang your own lock. Two people are needed to replace the film knife.

## Installation requirements {#sealer5-installation}

The Marten S-74 needs a 230 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 800 kg per square metre. Keep 60 cm free on every side for service access. The room must stay between 10 and 34 °C, with a relative humidity below 70%.

## Start-up procedure {#sealer5-startup}

1. Check that the front guard is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the jaw cooling air and wait until the sealing jaw is below 19 °C.
4. Run the homing cycle from the operator panel. It takes about 2 minutes.
5. Load program P144 for a test run, and check the first part before you start a batch.

## Calibration {#sealer5-calibration}

Calibrate the Marten S-74 every 3 months, and after any crash or part replacement. Use calibration tool CT-73 and the reference block RB-101. The measured jaw temperature must be within ±1% of the set value; if it is not, adjust offset parameter K63 and repeat. Write the result in the machine log.
