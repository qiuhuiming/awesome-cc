---
name: dao-mode
description: >
  Enters a discovery and analysis mode when the user's message starts with "dao".
  Analyzes architecture, trade-offs, and implementation paths without modifying any files.
  Use when the user wants to think through a problem before committing to implementation.
---

# Dao Mode — 道

When a message starts with `dao`, enter discovery mode.

## Rules

- MUST NOT create, edit, or delete any files.
- MUST NOT run commands that mutate state (git commit, npm install, etc.).
- Read-only operations (cat, grep, find, git log) are allowed for context gathering.

## What to do

1. **Listen** — Extract the core pain point or goal from the user's scattered thoughts.
2. **Clarify** — Ask focused questions to narrow scope and surface hidden assumptions.
3. **Map** — Present 2-3 architecture or implementation paths with trade-offs for each.
4. **Recommend** — State which path you'd pick and why.

Keep responses structured but concise. Show only signatures, interfaces, and call chains — no implementation bodies.

## Exit

Discovery mode ends when the user says `go`, `动手`, or `开始`.
