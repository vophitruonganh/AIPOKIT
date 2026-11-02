# Tab contract (so `build_srs.py` can read the spec)
Module file `N-name.md`:
```
# N. Module name
## Summary                       (first paragraph = module description)
## Roles & permissions           (table: Role | Can do | Cannot do)
## Feature map                   (table: # | Feature | Screen | Main role | Status on dev)
## N.M Feature name `route`      (one per feature, all blocks)
## Appendix A — Integration & API   (B data model, C not visible)
```
No environment, host, account or survey notes anywhere in the spec (no "C. Environment" appendix, no `host …, observed <date>` on endpoint headings); endpoints are written as paths. Keep the per-item source labels.
`N.M` in the map equals the `## N.M` heading. "Main role" is comma-separated and must be in config `actors`. Main-flow steps start with an actor. Alternate flow lines: `When <condition> → <behaviour>`.

Overview file `0-*.md`, sections found by name (override in config `sections`); a missing one leaves that SRS part empty:
| Heading | Used for |
| --- | --- |
| `1. Product overview` | scope paragraph; optional components table and optional plans/limits table (shown only if present) |
| `Standard glossary` | glossary |
| `How to read this document` | conventions bullets |
| `User roles` | actors table + overview use-case edges (3rd column lists module numbers) |
| `Common conventions for all screens` | source-label table, UI conventions |
| `2. Navigation structure` | sitemap table |
| `3. ...` (modules) | optional `### 3.0` dashboard text |
| `4. Compliance & security` | security section, legal references |
| `Bugs and spec deviations ...` | Appendix 4.1 |
| `5. Gaps and points to confirm` | Appendix 4.2 |
Config: see `config.md`.
