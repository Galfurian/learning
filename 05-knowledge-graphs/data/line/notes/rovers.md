# Rovers

## Rovers Missions {#rovers-missions}

Rover R-1, also called the first rover, serves bay 5 and moves a board from the warehouse to pallet 7. StartMission requires the rover to be idle; the Busy flag in the Status folder of R-1 reports that condition. Rover R-2 serves bay 5 too, but it does not serve bay 3. Charge either rover for twenty minutes after four missions.

## Rovers Confirm {#rovers-confirm}

The delivery mission is confirmed by the LastResult flag in the Status folder of R-1. The second rover, also called R-2, can move a cover to pallet 7. It then waits for bay 5 before returning to the charging point. Do not swap the two mission names in the supervisor configuration.

## Rover1 Return Route {#rover1-return-route}

R-1 can collect a spare tray from the warehouse and return it to bay 1. It leaves the charging point only after the safety scanner is clear. The supervisor checks the mission name against the pallet label. If the scanner stays blocked, the rover waits; it does not push the pallet or enter the inspection cell.

## Rover2 Fixture Route {#rover2-fixture-route}

R-2 carries a board to the fixture station at bay 4 during a recovery cycle. The operator confirms the fixture is empty before sending the rover. A second trip is allowed only after the first result is recorded. The route is deliberately different from the normal delivery route, which makes the two rover notes easy to confuse.
