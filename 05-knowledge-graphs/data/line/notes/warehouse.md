# Warehouse

## Warehouse Operations {#warehouse-operations}

The Vertical Warehouse serves bay 5. ExtractTray requires the warehouse to be idle; the Busy flag in the Status folder tells the controller when that condition holds. The method moves a tray to the operator bay. SendBack also moves a tray. Wait ten seconds after the lift stops before opening the bay door.

## Warehouse Reset {#warehouse-reset}

The warehouse alarm reset uses ResetAlarms. Its operation needs the stock-ready condition; the StockReady flag in Inventory tells the operator when it holds, and the method returns a completion flag. The operator must check that no person is inside the lift before starting a tray cycle.

## Warehouse Replenishment {#warehouse-replenishment}

A replenishment tray enters the Vertical Warehouse through bay 1. The operator checks the tray label, closes the lift door, and waits for the position display to settle. The warehouse can hold ten trays. A missing label is a stock problem, not a motion fault, so the operator records it before calling maintenance.

## Warehouse Distractor {#warehouse-distractor}

The Vertical Warehouse checks tray height before a lift cycle. The normal lift time is forty seconds, and the operator bay light remains on for ten seconds after arrival. Keep hands outside the shutter. A tray that feels unusually heavy is isolated for a stock check rather than forced into position.
