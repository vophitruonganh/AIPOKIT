# Token rules (apply in every phase; accuracy gates stay on)
1. **Scripts, not reading.** Lint, stats, page numbers and the SRS build are deterministic scripts. Never read a whole spec to count, check structure or format; read their output only.
2. **Local files, not repeated doc reads.** Export a tab once, then use Grep/Read with offsets on the file. Read a doc tab through the connector only to write back, and then only the feature section (`sinceRev` for changes).
3. **Load lazily.** Read one reference per phase (`playbook.md` section, `feature-block-standard.md` only when writing). Agents read the safety rules from the file; do not paste them into briefs.
4. **Small, exact briefs.** Give an agent: scope (module + feature ids), file paths, account/role, output format. No history, no project recap.
5. **Short returns.** Agent reports: tables or lists, under 200 words, paths and ids instead of content. Findings go into the doc/files, not the chat.
6. **Work in batches.** Verifier groups open questions by screen (open each screen once); writers update one feature per write; doc writes in batches.
7. **Right-size agents.** Do not hardcode models. Before spawning an agent run `python3 -I scripts/route_model.py <tool> <task> key=value...` (see `references/model-routing.md`) and pass the returned model and effort to that agent; `inherit` means leave it unset. At most 4 agents in parallel.
8. **Gate before polish.** Lint must pass before review; review only modules that passed; deepen only the lowest-scoring features; skip Phase 4 rows already answered.
9. **No loops.** Fix each lint FAIL once, then re-lint; do not re-read untouched features.
Accuracy guards that never get skipped: source labels, lint gate, three allowed answer prefixes, safety rules, privacy grep before delivery.
