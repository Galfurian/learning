# Qc

## Qc Route {#qc-route}

The Camera Quality Cell serves bay 5. CheckPallet requires cond:qc/idle, observed by qc/Status/Busy, and confirms mission:qc/inspect-pallet through qc/Inspection/Passed.

## Qc Result {#qc-result}

The QC mission:qc/inspect-pallet is confirmed by qc/Inspection/Passed. The camera cell moves item:board to the finished pallet record.
