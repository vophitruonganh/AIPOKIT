---
description: Change list between two versions of a spec. Usage - /po-kit-spec:diff <old md folder> <new md folder> [lang]
argument-hint: <old md folder> <new md folder> [lang]
allowed-tools: Bash(python3:*)
---
Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/spec_diff.py <old> <new> changes.md [lang]` for: $ARGUMENTS
Summarize the counts from the output in the user's language and give the path of `changes.md`. Do not read the spec files.
