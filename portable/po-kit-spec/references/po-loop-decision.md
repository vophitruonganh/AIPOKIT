# Optional PO loop: use it or skip it
The PO loop (Phase 6: `workflow `po-sheet`` then `workflow `po-import``) is an extension, not a step of every run. It costs the Product Owner time, so it is offered only when the decisions it collects will be used.

## When to decide
Once, right after the Phase 5 export is delivered. Never before: the user should first see the document.

## Inputs (no reading of the spec)
- **Purpose** from `brief.md`: `as-is record` (understand, onboard, audit, compare) or `basis for work` (build, rebuild, change, write tests, hand to an outsourcer).
- **Counts** from `python3 -I <scripts>/po_sheet_export.py <md dir> --count`: open questions (and how many High), proposed rules, owners.

## Recommendation
| Purpose | Open High questions + proposed rules | Recommend |
| --- | --- | --- |
| as-is record | any | skip: the document already lists what is to confirm |
| basis for work | 0 | skip: nothing blocks the work |
| basis for work | 1 or more | use, limited to High questions and proposed rules |
| unknown | any | skip, and say in one sentence when it would help |

## How to ask
One sentence in the delivery message, in the user's language, with the counts and the recommendation, for example: "The SRS is ready. 12 High questions and 9 proposed rules need a product decision before development; do you want a decision sheet for the PO (recommended), or keep the document as is?" Then:
- **No answer, or no**: skip. Do not ask again for this version. The commands stay available whenever the user asks.
- **Yes**: run `workflow `po-sheet``. If the recommendation was "limited to High", say so and keep Medium/Low rows out of the PO's way (filter on the Priority column).
- The user may also ask for the loop at any time; then run it without re-deciding.
