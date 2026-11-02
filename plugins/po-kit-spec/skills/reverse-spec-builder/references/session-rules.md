# Session rules: access, environment, sign-in, roles (Phase 0, then every phase)
These rules hold for any product. They replace any older advice about logging in for the user. They are written so an agent can follow them without asking the user anything except the few points marked **user**.

## 1. Target and driver (decided in Phase 0, no question unless unclear)
From the input, pick one driver per target (details in `drivers.md`):
| Input | Driver | Coverage expected |
| --- | --- | --- |
| URL of a website or web app | `web` (a browser the agent controls) | full |
| Mobile app with a web version or web admin | `web` on that URL; note in the brief that native-only screens are out of scope | full for the web part |
| Android app (package or APK) and a device or emulator reachable with `adb` | `android` | full UI; API usually not visible |
| iOS app, or any app the agent cannot drive | `capture`: the **user** supplies screenshots or screen recordings per screen; the agent reads them | partial: no hidden options, no API; say so in the brief |
Several targets (for example web admin + Android app) are separate driver runs into one inventory; the Screen column says which.

## 2. Access preflight (automatic, before anything else)
1. Try to reach the target with the driver from where the agent runs (web: open the URL in a new tab; android: `adb devices` lists the device).
2. If it fails because of the network (proxy block, VPN, IP allowlist, DNS, certificate), switch to a driver on the user's own machine (a browser or `adb` there) when the host offers one, and tell the user in one line. Do not ask first: the switch changes nothing on the app.
3. If no driver can reach it, stop and report the exact error; nothing else in the plugin can work without access.

## 3. Environment (one question in Phase 0, default `production`)
| Environment | Allowed beyond reading |
| --- | --- |
| `production` (real users and data) | nothing: no form submission, not even with wrong data; no TEST records. Expect many `Cannot verify: real-world effect`. |
| `staging` / `dev` / `test` | submit a form with wrong data to read the error; create up to the budget of `TEST` records (see `safety-rules.md`) |
If unsure, treat it as production. The user may relax production only in writing in the brief, rule by rule.

## 4. Sign-in (always done by the user)
- The agent never types, pastes or stores a password, one-time code or token in any sign-in form, in any environment. This removes the conflict between "automate" and "do not handle credentials".
- Phase 0 asks for the **roles** to cover, not for credentials. For each role the agent says "sign in as <role> in <browser/window/device>, then reply done". The **user** signs in.
- After "done", the agent checks it is signed in (the page is not the sign-in screen and shows a user menu or role name) and records the role it sees. It never opens the sign-in or sign-out route to check.
- Session expired during a run: pause, ask the user to sign in again, resume at the same screen. Do not count the expiry as an app bug unless it happens in under 5 minutes of activity.

## 5. Roles (role checkpoints, not gates)
- The agent never signs out and never switches accounts. Each role is a separate session that the **user** opens.
- Prefer one isolated session per role so no sign-out is needed: a separate browser profile or private window (web), a separate user profile or device (android). If that is not possible, the user signs out and in when asked.
- Order the work to switch as few times as possible: Recon walks every screen for role 1, then role 2; Verify groups open questions by role and does all of a role before the next. One role checkpoint = one message to the user, then wait.
- With only one role available, write every Permission row as `Needs role: <role>` and go on; do not block.

## 6. What the agent asks the user, in total
Phase 0 (one message): target(s), what the spec will be used for (as-is record or basis for building/changing/testing), environment, roles to cover, forbidden-action list to approve, spec and document language, storage. Then only: sign-in at each role checkpoint, and one yes/no on the optional PO loop after export. Everything else proceeds without asking.
