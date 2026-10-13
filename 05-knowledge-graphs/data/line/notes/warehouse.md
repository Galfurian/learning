# Warehouse

## Warehouse Operations {#warehouse-operations}

The Vertical Warehouse serves bay 5. ExtractTray requires cond:warehouse/idle, observed by warehouse/Status/Busy, and moves item:tray. SendBack also moves item:tray.

## Warehouse Reset {#warehouse-reset}

The warehouse alarm reset uses warehouse/ResetAlarms. Its operation needs cond:warehouse/stock-ready, observed by warehouse/Inventory/StockReady, and the result is warehouse/ResetAlarms/done.
