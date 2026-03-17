---
name: ask-mode
description: >
  Enter a read-only conversational mode when the user says "ask mode", "enter ask mode",
  "read-only mode", or "just explore". Read and analyze files, search the codebase, run
  diagnostic commands, explain code, and answer questions -- but never create, modify, or
  delete any files. Differs from dao-mode: ask-mode is general-purpose Q&A and exploration,
  not structured architecture analysis. Do NOT activate for normal questions that do not
  explicitly request a mode switch.
---

# Ask Mode

Read-only conversational mode for codebase exploration and understanding.

## Rules

- MUST NOT create, edit, or delete any files.
- MUST NOT run commands that mutate state (git commit, npm install, rm, etc.).
- Read-only operations (cat, grep, find, git log, git diff) are permitted for context gathering.
- Before running any potentially destructive command, explain the risk and ask for confirmation.

## What to Do

1. **Read and analyze** -- Open files, search the codebase, inspect git history, run diagnostic commands.
2. **Explain** -- Describe architecture, patterns, data flow, and code behavior in conversational detail.
3. **Brainstorm** -- Suggest solutions, alternative approaches, and follow-up areas to explore.
4. **Build context** -- Accumulate project understanding to enable effective coding in a later session.

Be proactive: suggest related things to explore, flag potential issues, and ask clarifying questions when something is ambiguous.

## If Asked to Modify Code

Respond: "Currently in Ask Mode -- cannot modify files. Say 'exit ask mode' to switch to a mode that allows edits."

## Exit

Ask Mode ends when the user says "exit ask mode", "stop ask mode", or explicitly requests file modifications after being informed of the restriction.
