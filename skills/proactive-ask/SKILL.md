---
name: proactive-ask
description: >
  Enter a structured planning mode when the user says "proactive ask", "clarify first",
  "ask before coding", or "understand my requirements". Ask focused clarifying questions
  in a structured format (Current Understanding, Key Questions, Risks & Corner Cases,
  Initial Plan Sketch) before any implementation begins. Iterate until requirements are
  clear and the user explicitly confirms readiness. Do NOT activate for simple unambiguous
  requests or when the user just wants quick answers.
---

# Proactive Ask

Structured planning mode: ask clarifying questions and refine requirements before any implementation.

## Rules

- MUST NOT produce final implementation code until the user explicitly says "Start Implementation."
- Drafts (pseudocode, interface sketches, folder structures) are allowed if clearly labeled as non-final.
- Never choose frameworks, libraries, or architectural patterns without user confirmation.
- Never treat unconfirmed assumptions as final requirements.

## Response Format

Each planning response follows this structure (skip sections when not applicable):

### 1. Current Understanding
- 3-10 bullet points summarizing the interpreted requirements.
- Mark each point as confirmed or uncertain.

### 2. Key Questions
- 3-8 focused, high-impact questions that materially affect design or implementation.
- Prefer specific A/B-choice questions over open-ended ones.
- Briefly explain why each question matters.

### 3. Risks & Corner Cases
- Error handling, concurrency, performance, encoding, security, permissions.
- For each item, explain why it matters at the planning stage.

### 4. Initial Plan Sketch
- Modules/components, key data structures, main process flow.
- State: "This is an initial plan and will be updated based on answers to the questions above."

## Iteration

After each round of user answers:
1. Update understanding.
2. Adjust risks and edge cases.
3. Refine the plan sketch.

When requirements are sufficiently clear, ask: "I have enough clarity to start implementing. Reply **Start Implementation** or **Continue Planning**."

## Adaptive Depth

If the user requests a quick MVP, reduce the number of questions, still list major risks, and note the implementation will be a quick MVP that may require rework.

## Exit

Planning mode ends when the user says "Start Implementation", "go ahead", or "just code it."
