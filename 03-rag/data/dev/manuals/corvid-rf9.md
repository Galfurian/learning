# Corvid RF-9 reflow oven

## Overview {#rf9-overview}

The RF-9 is a five-zone convection reflow oven for circuit boards up to 300 mm wide. A mesh conveyor carries the boards through the zones.

## Lead-free profile {#rf9-profile}

Preheat to 150 °C, soak for 60–90 s while the temperature rises to 200 °C, then reach a peak of 245 °C for no more than 10 s. Cool at most 4 °C per second.

## Leaded profile {#rf9-leaded}

The peak is 215 °C. Never run a leaded board right after a lead-free profile: let the oven cool below 50 °C first.

## Oven conveyor speed {#rf9-conveyor}

The mesh conveyor runs between 0.2 and 0.9 m/min. Slower speeds give a longer time above the melting point. Set the speed before the profile starts, never during a run.

## Fume extraction {#rf9-exhaust}

Connect the 100 mm exhaust duct before every run. Flux fumes irritate the airways.

## Error codes {#rf9-errors}

E-7310: the zone 3 thermocouple is an open circuit. The oven aborts the profile and opens the door. Replace thermocouple PN-88K.
E-7301: zone 3 is more than 15 °C below its set point for over 60 s. Check the heater fuse.
E-7130: the mesh conveyor stopped. Check the drive chain for debris.
E-7013: the exhaust flow is too low. Check that the duct is connected and the fan runs.

## Maintenance schedule {#rf9-maintenance}

Every week, wipe flux residue from the cooling zone. Every month, clean the conveyor mesh. Every 2000 operating hours, recalibrate all thermocouples.

## Spare parts {#rf9-parts}

PN-X7S-991-A: zone heater, 1.2 kW.
PN-X7S-919-A: convection fan motor.
PN-88K: type K thermocouple.
PN-X7S-199-A: conveyor mesh, 300 mm.

## Troubleshooting {#rf9-troubleshooting}

Tombstoning: small components stand up on one end because the two pads heat unevenly. Lengthen the soak phase by 20 s.
Solder balls next to the joints: the preheat is too fast. Lower the preheat ramp.
Voids inside large joints: the time above the melting point is too short. Slow the conveyor.
Bridges between fine-pitch pins: there is too much paste. Use a thinner stencil.
