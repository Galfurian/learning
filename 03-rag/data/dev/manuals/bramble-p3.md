# Bramble P3 3D printer

## Overview {#p3-overview}

The P3 is a filament 3D printer with a 250 × 250 × 250 mm build volume, a 0.4 mm nozzle and a heated bed. It prints from SD card or over the network.

## Supported filaments {#p3-filaments}

PLA, PETG and TPU. ABS needs the enclosure kit PN-31C because it warps in open air.

## Nozzle temperatures {#p3-temps}

PLA 200–215 °C, PETG 235–245 °C, TPU 225 °C. Do not exceed 260 °C: above that the PTFE liner in the hotend degrades.

## Bed levelling {#p3-bed}

Run the 9-point probe after every nozzle change. If the first layer does not stick, raise the bed temperature by 5 °C and clean the build sheet with soap and water.

## Part cooling fan {#p3-cooling}

Set the fan to 100% for PLA, 30% for PETG, and off for the first layer. Too much cooling on PETG weakens the bond between layers.

## Error codes {#p3-errors}

E-2201: thermal runaway. The hotend temperature did not rise as expected. Check the heater cartridge connector and the thermistor PN-12T.
E-2210: the bed thermistor reads an open circuit. Check the bed cable at the rear connector.
E-2102: the filament ran out. Load a new spool and press CONTINUE.
E-2012: the Z endstop did not trigger during homing. Check that nothing blocks the endstop lever.

## Maintenance schedule {#p3-maintenance}

Every week, clean the build sheet. Every 200 operating hours, lubricate the Z lead screw with PTFE grease. Every 500 operating hours, replace the nozzle.

## Spare parts {#p3-parts}

PN-X7R-991-A: nozzle, 0.4 mm, hardened steel.
PN-X7R-991-B: nozzle, 0.6 mm, hardened steel.
PN-X7R-919-A: heater cartridge, 24 V 40 W.
PN-12T: hotend thermistor.
PN-31C: enclosure kit for ABS.

## Troubleshooting {#p3-troubleshooting}

The extruder clicks and lines are thin or missing: the nozzle is clogged. Heat it to 240 °C and do a cold pull with nylon filament.
Thin strings appear between parts: retraction is too short. Raise it by 0.5 mm at a time.
The corners of the part lift from the bed: the part is warping. Use a brim, and keep the room free of drafts.
Layers are shifted sideways: a belt is loose or the print head hit the part. Tighten the belts and check for curled edges.
