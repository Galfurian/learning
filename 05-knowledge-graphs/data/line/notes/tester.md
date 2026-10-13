# Tester

## Tester Route {#tester-route}

The Board Tester serves bay 2 and moves a board to the Engraving Cell. BoardIn requires the tester to be ready; the Busy flag in its Status folder reports that condition. The input clamp takes six seconds to close and must be empty before a new board arrives.

## Tester Result {#tester-result}

The board test mission is confirmed by the TestPassed flag in the Boards folder. RunTest returns a submitted result before the measurements finish. A failed test keeps the board at the output station until a technician records the reason.

## Tester Fixture Return {#tester-fixture-return}

The Board Tester uses bay 3 for a fixture return. A technician removes the reference board, checks its serial number, and closes the clamp. The test recipe has a five-second settle time and a twenty-second measurement window. A board with a missing serial stays at the input station until the record is corrected.

## Tester Distractor {#tester-distractor}

The Board Tester stores a result for thirty days. Its reference board is checked at the start of each morning shift and replaced after one hundred cycles. The test operator wears an antistatic strap. A clean clamp improves repeatability, but cleaning never replaces the scheduled calibration.
