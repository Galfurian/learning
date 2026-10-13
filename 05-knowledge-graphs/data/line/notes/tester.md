# Tester

## Tester Route {#tester-route}

The Board Tester serves bay 2 and moves item:board to cell:cnc. BoardIn requires cond:tester/ready, observed by tester/Status/Busy.

## Tester Result {#tester-result}

The test mission:tester/board-test is confirmed by tester/Boards/TestPassed. RunTest returns tester/Boards/RunTest/started.
