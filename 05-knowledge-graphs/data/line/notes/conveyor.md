# Conveyor

## Conveyor Route {#conveyor-route}

The Loop Conveyor serves bay 1 and bay 2. MovePallet moves pallet:7 to bay:1, then to bay:2. The conveyor requires cond:conveyor/ready, observed by conveyor/Status/Busy.

## Conveyor Alarms {#conveyor-alarms}

The conveyor alarm:conveyor/NoAirPressure stops assembly and alarm:conveyor/MotorTrip stops qc. ResetAlarms fixes both alarms after the line is safe.
