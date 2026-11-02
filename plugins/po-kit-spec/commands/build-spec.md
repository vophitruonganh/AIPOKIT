---
description: Build a verified product spec from any running website, web app or mobile app (phases 0-4). Usage - /po-kit-spec:build-spec <URL, app id or captures folder>
argument-hint: <URL, app id or captures folder>
---
Run the `reverse-spec-builder` skill for: $ARGUMENTS

First read `.po-kit/standards.md` if it exists (if not, mention once that `/po-kit-spec:setup-standards` records the team's own process and templates).
Phase 0, in this order:
1. Without asking: pick the driver and run the access preflight from `references/session-rules.md` and `references/drivers.md`. If the network blocks the target, switch to a driver on the user's machine and say so in one line; if nothing reaches it, stop and report the error.
2. ONE message for anything still missing: target(s), what the spec will be used for (as-is record, or basis for building/changing/testing), environment (production / staging / dev; default production), the roles to cover (never ask for passwords: the user signs in at each role checkpoint), the forbidden-actions list (show the defaults from `references/safety-rules.md`; forbid saving/submitting, not opening forms, and state the coverage cost of anything stricter, see `references/coverage-rules.md`), storage (Claude Doc with one tab per module, or a markdown folder), and the **spec language** and **document language** (default: the user's language).
3. After the user approves the forbidden list (the only gate), ask them to sign in as the first role, then work without asking. Stop only at role checkpoints (sign in as the next role) and when access is lost (session expired, device gone).

Model choice: do not hardcode models. Before each agent call, follow `references/model-routing.md` (`scripts/route_model.py`) to get a model tier and effort from the task's measured complexity, and pass them on that call.
