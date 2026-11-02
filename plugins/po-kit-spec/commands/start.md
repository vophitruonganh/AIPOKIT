---
description: Start here. Pick the website or the running app to document (an open browser tab, a URL, an Android app on a connected device, or a screenshots folder), then run the whole workflow. Usage - /po-kit-spec:start [URL | app | folder]
argument-hint: [URL | app | folder] (optional)
---
Entry point for a Product Owner. Input: $ARGUMENTS

1. **Target given** (a URL, an Android package or app name, or a folder of screenshots): use it and go to step 3.
2. **No target given**: build ONE numbered menu from what is running now, read-only, and ask the user to pick a number or paste a URL:
   - **Open browser tabs**: if a browser tool that lists tabs is available, list the user's open `http(s)` tabs as `title — host/path` (no query strings, at most 15, skip sign-in pages and browser-internal pages). Do not read their content.
   - **Android**: if `adb` is available, for each device in `adb devices` show the foreground app (`adb shell dumpsys activity activities | grep -m1 mResumedActivity`) as `Android: <app label or package> on <device model>`.
   - **Always add**: `Enter a URL`, `Use screenshots or screen recordings from a folder` (for iOS or any app that cannot be driven), and, if a `.po-kit/` spec folder already exists here, `Update the existing spec of <product>` (an update run).
   If nothing is detected, show only the always-added entries. Never open, reload or close any tab to build the menu.
3. **Confirm in one line**: "I will document <target> with the <web | android | capture> driver." A tab the user picked becomes the target URL (its origin and route); the agent works in its own new tab or window, never in the user's tab.
4. Run `/po-kit-spec:build-spec <target>` from Phase 0 (access preflight, one message of questions, forbidden list, sign-in per role). For an update run, follow the update rules in `references/coverage-rules.md`.
5. When Phase 4 is done, run `/po-kit-spec:export-srs` with the configured layout and follow its step on the optional PO loop.
