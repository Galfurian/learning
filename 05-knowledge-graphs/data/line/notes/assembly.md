# Assembly

## Assembly Route {#assembly-route}

The Assembly Cell serves bay 4 and moves item:cover-top and item:cover-bottom onto pallet:7. Assemble requires cond:assembly/idle, observed by assembly/Status/Busy.

## Assembly Confirm {#assembly-confirm}

The assembly mission:assembly/fit-covers is confirmed by assembly/Status/LastResult. Screw requires cond:assembly/screwdriver-ready, observed by assembly/Status/Busy.
