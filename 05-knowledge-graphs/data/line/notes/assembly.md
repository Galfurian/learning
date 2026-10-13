# Assembly

## Assembly Route {#assembly-route}

The Assembly Cell serves bay 4 and moves a top cover and a bottom cover onto pallet 7. Assemble requires the cell to be idle; the Busy flag in its Status folder reports that condition. The two arms must report home before the pallet enters the fixture.

## Assembly Confirm {#assembly-confirm}

The assembly mission is confirmed by the LastResult flag in the Status folder. Screw requires the screwdriver to be ready; the Busy flag changes while the program runs. Replace the bit after two hundred cycles and record the program number in the shift log.

## Assembly Rework Route {#assembly-rework-route}

A rework pallet may return to bay 5 beside the Assembly Cell. The operator removes the top cover before opening the fixture. The screwdriver program is selected from the job card, and the two arms remain in their home poses during the check. Rework parts are counted separately from first-pass parts.
