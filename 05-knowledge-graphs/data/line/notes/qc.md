# Qc

## Qc Route {#qc-route}

The Camera Quality Cell serves bay 5. CheckPallet requires the inspection cell to be idle; the Busy flag in its Status folder reports that condition. The method confirms the pallet inspection through the Passed flag in Inspection. The camera takes twelve seconds to scan one pallet.

## Qc Result {#qc-result}

The pallet inspection is confirmed by the Passed flag in the Inspection folder. The camera cell moves the board to the finished pallet record. If the result is false, keep the pallet in bay 5 and ask quality staff to review the images before releasing it.

## Qc Recheck Route {#qc-recheck-route}

The Camera Quality Cell can recheck a pallet at bay 4. The quality operator cleans the lens, confirms the lighting reference, and repeats the inspection once. A second failure sends the pallet to manual review. The image archive keeps the serial number and the shift name, but it does not change the production route.

## Qc Distractor {#qc-distractor}

The Camera Quality Cell uses two lights and one fixed lens. The reference image is renewed every Monday or after a lens change. Keep reflective tools outside the field of view. A clean image does not prove that a pallet passed; the operator must read the recorded result and follow the review rule.
