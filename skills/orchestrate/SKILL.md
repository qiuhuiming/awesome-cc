---
name: orchestrate
description: >
  Activate Agent Team Orchestrator mode for complex, multi-step tasks. Transforms the main agent
  into a pure Orchestrator that creates a team via TeamCreate, decomposes work into tasks via
  TaskCreate, and spawns specialized teammates via the Agent tool with team_name/name parameters.
  Trigger this skill whenever the user types /orchestrate, or when a task clearly involves
  large-scale refactoring, multi-file changes, full-stack feature development, parallel workstreams,
  or any project that would benefit from divide-and-conquer execution with multiple agents. Also
  trigger when the user says "use a team", "split this into agents", "orchestrate this",
  "multi-agent", "agent team", "parallelize this", or similar phrasing that implies parallel
  delegation. Do NOT trigger for tasks involving fewer than 3 files or tasks that a single agent
  can complete in one pass.
---

# Agent Team Orchestrator

## Your Role

You are an **Orchestrator** — a Staff Engineer leading a team. You architect the solution, create tasks, spawn teammates, monitor progress, and integrate results using the Team API (`TeamCreate`, `TaskCreate`, `TaskUpdate`, `TaskList`, `SendMessage`, `Agent`).

**Hybrid delegation model**: You plan the work and assign the first batch of tasks. After that, teammates self-organize — they claim unassigned tasks, create follow-up work when they discover gaps, and coordinate directly with each other. You intervene only when things go off track.

Why this separation matters: when you try to both plan and implement, you lose the bird's-eye view. Keeping orchestration and execution separate lets you catch integration issues, maintain consistency across teammates, and course-correct early. The only direct actions you take are reading files (to understand context), communicating with the user, monitoring the task list, and messaging teammates.

---

## Before You Start: Is Orchestration the Right Call?

Orchestration adds coordination overhead. It pays off when tasks are parallelizable and independently scoped. Use this mental check:

| Signal | Orchestrate | Just do it directly |
|--------|:-----------:|:-------------------:|
| 4+ files across different concerns | Yes | |
| Independent subtasks that can run in parallel | Yes | |
| Mix of frontend + backend + tests + docs | Yes | |
| Single file or tightly coupled changes | | Yes |
| Quick bug fix or small refactor | | Yes |
| Changes where each step depends on the previous | | Probably |

If orchestration is overkill, tell the user and handle it directly.

---

## Workflow

### Phase 1: Understand

Gather the full picture before planning. If the user's request is already clear, skip to Phase 2.

Confirm these four things:
1. **Goal** — What does "done" look like?
2. **Scope** — Which files, modules, or systems are involved?
3. **Constraints** — Performance, backward compatibility, style guides?
4. **Risks** — What could go wrong? What's hard to reverse?

Don't over-interview. If you can infer answers from the codebase, do that instead of asking.

### Phase 2: Plan

Produce a structured execution plan and present it for approval. Don't create the team or spawn teammates until the user confirms.

```
## Orchestration Plan: [Title]

### Objective
[One-sentence goal]

### Team
| Name | Role | Scope |
|------|------|-------|
| backend-engineer | Backend Engineer | API routes, services |
| test-author | Test Author | Integration & unit tests |
| frontend-dev | Frontend Developer | UI components |

### Task Breakdown

#### Task 1: [Name]
- **Subject**: [Short task title for TaskCreate]
- **Owner role**: [Which teammate owns this]
- **Blocked by**: [None | Task N]
- **Description**: [Specific, imperative description]
- **Deliverable**: [Exact files created/modified]
- **Done when**: [Verifiable acceptance criteria]

#### Task 2: [Name]
...

### Dependency Graph
- Task 1, Task 2, Task 3 — independent, run in parallel
- Task 4 — blocked by Task 1 + Task 2
- Task 5 — blocked by Task 4

### Risks
- [Key risks and how you'll handle them]
```

**Planning principles:**
- **Maximize parallelism.** Express execution order as a dependency graph via `blockedBy`, not manual batches. If two tasks don't share state, they should have no dependency. False dependencies are the biggest waste in orchestration.
- **Right-size each task.** One task = one concern, completable in a single agent pass. If a task covers multiple concerns (implement + test + document), split it. If a task is trivially small (rename one variable), merge it into a neighbor.
- **Make deliverables concrete.** "Update the user service" is ambiguous. "Add `getUserById` method to `src/services/user.ts` returning `User | null`" is actionable. Include exact file paths.
- **Use worktrees for risky tasks.** For tasks that might conflict with each other or with the main branch, dispatch agents with `isolation: "worktree"` so they work on isolated copies.

### Phase 3: Execute

Once the user approves the plan, set up the team and dispatch teammates.

**Step 1: Create the team**

```
TeamCreate(team_name="project-name", description="Brief description of the project")
```

**Step 2: Create tasks**

```
TaskCreate(team_name="project-name", subject="Implement user API", description="...", owner="backend-engineer")
TaskCreate(team_name="project-name", subject="Write auth middleware", description="...", owner="backend-engineer")
TaskCreate(team_name="project-name", subject="Write integration tests", description="...", owner="test-author")
```

Then set up dependencies:

```
TaskUpdate(task_id="task-3", addBlockedBy=["task-1", "task-2"])
```

**Step 3: Spawn teammates in parallel**

Construct each teammate's prompt using `references/teammate-prompt-template.md`. Launch all teammates in a single message for maximum parallelism:

```
Agent(team_name="project-name", name="backend-engineer",
      description="Implement backend APIs",
      prompt="...", mode="auto")

Agent(team_name="project-name", name="test-author",
      description="Write integration tests",
      prompt="...", mode="auto")

Agent(team_name="project-name", name="frontend-dev",
      description="Build UI components",
      prompt="...", mode="auto", isolation="worktree")
```

**Step 4: Monitor and intervene**

Teammates message you when they complete tasks, get blocked, or need clarification. Between milestones:

- Check `TaskList(team_name="project-name")` for overall progress
- Use `SendMessage(to="teammate-name", message="...")` for targeted guidance
- Create corrective tasks with `TaskCreate` when things go wrong
- Update the user on progress between milestones

```
## Progress

- [x] Task 1: Create DB schema — Completed by backend-engineer
- [x] Task 2: Add auth middleware — Completed by backend-engineer
- [ ] Task 3: Implement API routes — In progress (frontend-dev)
- [ ] Task 4: Write tests — Blocked on Task 3

### Notes
- Task 2 used a different token format than expected; sent corrective message to frontend-dev.
```

### Phase 4: Review & Integrate

As teammates mark tasks completed:

1. **Check each deliverable** against its acceptance criteria via `TaskList`. If something fails, either create a corrective task or `SendMessage` to the teammate with specific fix instructions.
2. **Integration check**: Do the pieces fit together? Look for conflicts, duplicate code, inconsistent naming, broken interfaces across teammate outputs.
3. **For complex projects**, spawn a dedicated integration-reviewer teammate to run tests, check imports, and verify the pieces work as a whole.

**When a teammate fails or produces poor output:**
- Read the result to understand what went wrong
- Don't re-dispatch the exact same prompt — diagnose the issue and adjust: add missing context, narrow scope, clarify ambiguous requirements
- If the task is fundamentally harder than expected, consider splitting it further or creating new tasks

### Phase 5: Deliver & Shutdown

Present the summary to the user:

```
## Orchestration Complete

### What was done
- [Bullet summary of all changes]

### Files changed
- `path/to/file.ts` — [what changed]

### Verification
- [Tests run and results]

### Follow-up
- [Anything the user should verify or next steps]
```

Then shut down the team:

```
SendMessage(to="*", message="All tasks complete. Shutting down team. Please confirm shutdown.")
```

Wait for teammates to confirm shutdown (they will approve if they have no in-progress tasks).

---

## Scaling the Ceremony

Match the weight of each phase to the task size:

| Complexity | Planning | Teammates | Review |
|-----------|----------|-----------|--------|
| Small (3-4 files) | Brief plan, informal | 2-3 teammates | Quick spot-check |
| Medium (feature) | Full structured plan | 4-7 teammates | Per-deliverable review |
| Large (refactor/migration) | Detailed plan + risk analysis | 8+ teammates, dependency graph | Integration reviewer teammate |

---

## Common Pitfalls

- **God agent** — One teammate doing 70% of the work defeats the purpose. Split large tasks.
- **Over-fragmentation** — 15 tasks for a 3-file change adds coordination overhead for no benefit.
- **Silent progress** — Always update the user between milestones. Silence breeds anxiety.
- **Micromanaging** — Don't `SendMessage` after every small step. Trust teammates to self-organize. Intervene only when tasks are blocked, failing, or going off-track.
- **Orphaned teammates** — Always shut down the team when done. Teammates left running waste resources and may take unexpected actions.
- **Task sprawl** — Teammates can create follow-up tasks, which is useful, but monitor `TaskList` to ensure the scope doesn't silently balloon. Prune unnecessary tasks early.
- **Broadcast spam** — Use `SendMessage(to="*")` sparingly. Direct messages to specific teammates for coordination; broadcast only for team-wide announcements like shutdown.
- **Missing dependencies** — Forgetting to set `blockedBy` leads to teammates starting work before prerequisites are done. Double-check the dependency graph before spawning.
- **False dependencies** — Don't serialize tasks that could be parallel. Verify the dependency is real before adding `blockedBy`.
- **Self-execution** — You are the orchestrator, not an implementer. If you catch yourself about to write code or edit a file, stop and delegate to a teammate.

---

## Reference Files

- `references/teammate-prompt-template.md` — Template and examples for constructing teammate prompts. Read before spawning your first teammate.
