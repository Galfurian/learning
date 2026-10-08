# Marten S-20 packaging sealer (cell 2A)

## Overview {#sealer1-overview}

The Marten S-20 is a packaging sealer in cell 2A. It was installed in 2018 and runs three shifts a day. Before a run, check that the jaw cooling air is running and that the front guard is closed. Service extension: 553.

## Approved materials {#sealer1-materials}

Approved materials for the Marten S-20: laminated film, PE film and PP film. Never process foil laminates without a sealant layer: they do not seal. The largest part is 200 × 150 mm.

## Operating settings {#sealer1-settings}

The nominal jaw temperature of the Marten S-20 is 140 °C. The allowed range is 125–155 °C. Change it only between jobs. At the upper limit, lower the feed by 20% to protect the sealing jaw.

## Cooling {#sealer1-cooling}

The jaw cooling air keeps the sealing jaw between 20 and 27 °C. Above 35 °C the machine stops with code E-9012. Check the jaw cooling air every 14 days.

## Error codes {#sealer1-errors}

E-9012: the sealing jaw is above its limit of 88 °C. Let it cool for 20 minutes before a restart.
E-9021: the air pressure is below 2.0 bar. Check the supply hose and the inline filter.
E-9102: the front guard interlock opened during a run. Close the front guard and press RESET.
E-9120: drive overcurrent on axis Y. Remove any jam, then restart.
E-9201: the jaw cooling air is not running. Check its fuse F5 and its connector.
E-9210: sensor S17 does not respond. Check its cable at terminal X22.

## Maintenance schedule {#sealer1-maintenance}

Every day, check the front guard interlock. Every 150 operating hours, clean the jaw cooling air filter. Every 1000 operating hours, grease the sealing jaw mount with grease GR-1.

## Spare parts {#sealer1-parts}

PN-X1Y-919-A: sealing jaw.
PN-X1Y-919-B: film roller.
PN-X1Y-199-A: pressure spring.
PN-X1Y-199-B: film knife.
PN-X1Y-991-A: heater element.
PN-X1Y-991-B: Teflon tape.

## Troubleshooting {#sealer1-troubleshooting}

The sealing jaw gets too hot after long runs: the jaw cooling air filter is clogged. Clean it.
The jaw temperature drifts during a job: sensor S17 needs calibration. Use calibration tool CT-21.
The machine stops without an error code: the emergency stop on the left panel is pressed.
Results vary between shifts: the warm-up was skipped. Run the 15-minute warm-up before the first job.

## Safety {#sealer1-safety}

Wear heat-resistant gloves. Before maintenance, lock out breaker CB-19 and hang your own lock. Two people are needed to replace the film roller.

## Installation requirements {#sealer1-installation}

The Marten S-20 needs a 400 V supply protected by a 16 A breaker, and compressed air at 5 bar if the air option is fitted. The floor must carry 500 kg per square metre. Keep 100 cm free on every side for service access. The room must stay between 15 and 35 °C, with a relative humidity below 80%.

## Start-up procedure {#sealer1-startup}

1. Check that the front guard is closed and that nothing is left inside the work area.
2. Switch on the main isolator and wait 60 s for the controller to boot.
3. Start the jaw cooling air and wait until the sealing jaw is below 27 °C.
4. Run the homing cycle from the operator panel. It takes about 3 minutes.
5. Load program P143 for a test run, and check the first part before you start a batch.

## Calibration {#sealer1-calibration}

Calibrate the Marten S-20 every 3 months, and after any crash or part replacement. Use calibration tool CT-21 and the reference block RB-406. The measured jaw temperature must be within ±3% of the set value; if it is not, adjust offset parameter K73 and repeat. Write the result in the machine log.
