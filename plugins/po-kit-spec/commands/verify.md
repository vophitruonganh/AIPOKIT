---
description: Phase 4. Verify the spec's open questions on the real product with safe actions. Usage - /po-kit-spec:verify <module or tab>
argument-hint: <module or tab>
---
Run Phase 4 for: $ARGUMENTS
Group the open questions by role, then by module. For each role: ask the user to sign in as that role (role checkpoint, `references/session-rules.md`), then run one `spec-verifier` per module, each in its own tab or session of that role, at most 4 in parallel. Brief each with: scope (module, feature ids, file path), driver, signed-in role, environment, the paths of `references/safety-rules.md`, `references/drivers.md`, `references/coverage-rules.md` and `inventory.md` (do not paste their text). When all roles are done, merge the bug lists into the bugs table, list leftover test records for engineering, and report counts of verified / partly / cannot verify. Do not ask the user to review Cannot verify items here: they go to the PO sheet (`/po-kit-spec:po-sheet`).
