# Rovers

## Rovers Missions {#rovers-missions}

Rover R-1, also called the first rover, serves bay 5 and moves item:board from the warehouse to pallet:7. StartMission requires cond:rover/idle, observed by rover1/Status/Busy. Rover R-2 serves bay 5 too.

## Rovers Confirm {#rovers-confirm}

The rover mission:rover/deliver-board is confirmed by rover1/Status/LastResult. The second rover, or R-2, can also move item:cover to pallet:7.
