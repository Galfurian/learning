# Cnc

## Cnc Route {#cnc-route}

The Engraving Cell serves bay 3 and moves item:board. PickBoard requires cond:cnc/idle, observed by cnc/Status/Busy.

## Cnc Confirm {#cnc-confirm}

The engraving mission:cnc/engrave-board is confirmed by cnc/Status/LastResult. PlaceBoard moves item:board to pallet:7.
