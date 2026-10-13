# Cnc

## Cnc Route {#cnc-route}

The Engraving Cell serves bay 3 and moves a board. PickBoard requires the CNC cell to be idle; the Busy flag in its Status folder reports that condition. The arm must approach from the marked side, and the spindle needs a thirty-second warm-up before engraving.

## Cnc Confirm {#cnc-confirm}

The engraving mission is confirmed by the LastResult flag in the Status folder of the Engraving Cell. PlaceBoard moves the board to pallet 7. Inspect the engraving depth every fifty boards and stop the cell if the depth is outside the work instruction.

## Cnc Recovery Route {#cnc-recovery-route}

The Engraving Cell can receive a recovery board at bay 2. The arm waits at its marked pose while the operator checks the spindle guard. Engraving a recovery board uses the same serial rule as normal production, but the result is recorded in a separate shift note. The cell must be empty before the next pallet arrives.
