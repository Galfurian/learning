# Conveyor

## Conveyor Route {#conveyor-route}

The Loop Conveyor serves bay 1 and bay 2. MovePallet moves pallet 7 to bay 1, then to bay 2. The line-ready condition is checked from the Busy flag in the Status folder before motion starts. A full loop takes about four minutes at the standard speed.

## Conveyor Alarms {#conveyor-alarms}

The low air pressure alarm of the Loop Conveyor stops the Assembly Cell, and its motor trip alarm stops the Camera Quality Cell. The ResetAlarms method clears both alarms after the guard is closed. Call the line supervisor if an alarm returns twice in one shift.

## Conveyor Return Bays {#conveyor-return-bays}

During a maintenance return, the Loop Conveyor handles bay 3 and bay 4. Pallet 8 is used for the empty-fixture check. The return operator reads the belt speed twice before releasing the pallet. A guard reset does not start motion by itself, and the supervisor must authorise the next cycle.

## Conveyor Distractor {#conveyor-distractor}

The Loop Conveyor uses a nominal speed of 18 metres per minute and a two-second pause at each stop. The drive cabinet is inspected at the start of every shift. A loose cover can cause vibration without raising an alarm. The operator records the sound and calls maintenance if it continues after cleaning.
