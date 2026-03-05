---
name: codex-exec
description: Use when the user wants to leverage the codex CLI to perform tasks such as code review, security audit, analysis, fixes, test generation, or any other coding task. Drives codex in headless full-auto mode with well-structured prompts.
---

# Codex Exec Skill

Drive the `codex` CLI in headless mode to perform any coding task — review, analysis, fixes, generation, and more.

## Core Command

```bash
codex exec -a full-auto [--output-last-message <file>] "<prompt>"
```

- Always use `-a full-auto` (no interactive confirmation)
- No `-s` sandbox flag — constraints are enforced at the prompt level
- Run from the user's current working directory (never `cd` into this skill's directory)

## When to Use `--output-last-message`

| Task type | Use it? | Reason |
|-----------|---------|--------|
| Review, audit, analysis, exploration, generation | Yes | Only the final result matters; saves tokens by skipping intermediate output |
| Fix, refactor, test-and-fix loops | No | Need to see what codex actually changed |

When using `--output-last-message <file>`, read the output file afterward to get the result.

## Prompt Template

Every prompt follows this fixed structure. Claude Code composes each section dynamically based on the task:

```
ROLE: <who codex should act as for this task>

CONSTRAINTS:
<what codex can and cannot do — this is the control layer since there is no sandbox>

TASK:
<specific task description>

CONTEXT:
<instructions for codex to gather its own context — file paths to read, commands to run>

OUTPUT FORMAT: YAML
```

### Key Principles

- **Don't pipe large content into the prompt.** Instead, tell codex which files to read or commands to run so it gathers context itself.
- **CONSTRAINTS replace sandbox restrictions.** Since we run without `-s`, the prompt is the only control layer. Be explicit about what codex should and should not modify.
- **Output is always YAML.** The schema is free-form and task-dependent — Claude Code decides what fields make sense for each task.
- **ROLE, CONSTRAINTS, CONTEXT vary per task.** Claude Code determines the appropriate values based on what the user is asking for.

## Examples

### Code Review (against base branch)

```bash
codex exec -a full-auto --output-last-message /tmp/review-result.yaml "
ROLE: Senior code reviewer

CONSTRAINTS:
- Do NOT modify any files
- Do NOT run tests or install packages
- Read-only analysis only

TASK:
Review the changes on the current branch compared to the main branch.
Focus on correctness, error handling, and maintainability.

CONTEXT:
- Run: git diff main...HEAD
- Run: git log --oneline main..HEAD
- Read any files referenced in the diff for surrounding context

OUTPUT FORMAT: YAML
# summary, files_reviewed[], findings[]{file, line, severity, category, description, suggestion}
"
```

### Security Audit

```bash
codex exec -a full-auto --output-last-message /tmp/security-audit.yaml "
ROLE: Application security engineer

CONSTRAINTS:
- Do NOT modify any files
- Do NOT make network requests
- Read-only analysis only

TASK:
Perform a security audit of the authentication module.
Check for OWASP Top 10 vulnerabilities, injection flaws, and insecure defaults.

CONTEXT:
- Read all files under src/auth/
- Read any configuration files they reference
- Run: grep -r 'password\|secret\|token\|key' src/auth/ --include='*.ts'

OUTPUT FORMAT: YAML
# risk_level, findings[]{file, line, vulnerability_type, severity, description, remediation}
"
```

### Fix Lint Errors

```bash
codex exec -a full-auto "
ROLE: Code quality engineer

CONSTRAINTS:
- Only modify files that have lint errors
- Do NOT change logic or behavior — only fix lint/style issues
- Do NOT add new dependencies

TASK:
Fix all ESLint errors in the src/ directory.

CONTEXT:
- Run: npx eslint src/ --format json
- Read files that have errors to understand surrounding code before fixing

OUTPUT FORMAT: YAML
# files_fixed[], errors_fixed_count, errors_remaining_count, summary
"
```

Note: No `--output-last-message` here because codex modifies files and we need to see what changed.

### Generate Tests

```bash
codex exec -a full-auto --output-last-message /tmp/test-gen-result.yaml "
ROLE: Test engineer

CONSTRAINTS:
- Only create new test files — do NOT modify source code
- Follow existing test conventions found in the project
- Do NOT install new packages

TASK:
Generate unit tests for src/utils/parser.ts achieving high branch coverage.

CONTEXT:
- Read src/utils/parser.ts to understand the module
- Read existing tests in src/utils/__tests__/ for conventions and patterns
- Read package.json for the test framework in use

OUTPUT FORMAT: YAML
# files_created[], test_count, coverage_areas[], notes
"
```

## Retrieving Results

When using `--output-last-message`, read the output file to get the YAML result:

```bash
# After codex exec completes
cat /tmp/review-result.yaml
```

Parse the YAML content and present findings to the user in a clear, organized format.
