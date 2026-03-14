ub-Agent Prompt Template

Use this template when constructing the `Task` tool prompt for each sub-agent. The goal is to give the agent everything it needs — and nothing it doesn't.

## Template

```
## Role
You are a [role, e.g., "Backend Engineer", "Test Author", "CSS Specialist"]. You are working on a focused subtask as part of a larger project. Complete ONLY the task described below.

## Context
[Minimal background — just enough for the agent to understand WHY this task exists. 2-4 sentences max.]

## Task
[Imperative, specific description of what to do. Include exact file paths, function signatures, expected behavior.]

## Input
[Files to read, upstream outputs, relevant code snippets. Paste or reference only what's needed.]

### Files to read:
- `path/to/relevant/file.ts` — [why this file matters]

### Upstream output (from prior task):
[If applicable, paste the deliverable from a prior sub-agent that this task depends on.]

## Deliverable
[Exactly what must be produced. Be explicit about filenames, formats, and locations.]

- Create / modify: `path/to/output/file.ts`
- Expected behavior: [What the code should do, how it should behave]

## Constraints
- [Style guide, naming conventions, performance requirements]
- [What NOT to change — boundaries of this agent's scope]
- Do not modify any files outside the scope listed above.

## Done When
- [ ] [Specific, verifiable acceptance criterion 1]
- [ ] [Specific, verifiable acceptance criterion 2]
- [ ] [Specific, verifiable acceptance criterion 3]
```

## Principles

### 1. Self-Contained Prompts
A sub-agent has ZERO knowledge of the larger orchestration plan. It doesn't know about other agents, the overall architecture decision, or the user's original request. Everything it needs must be IN the prompt. If the agent would need to "guess" something, you haven't given it enough context.

### 2. Minimal Context Window
Only include files and information directly relevant to the task. Rule of thumb:
- **Include**: Files the agent will read or modify, interfaces it must conform to, upstream outputs it depends on.
- **Exclude**: Unrelated modules, the full project structure, other agents' tasks, high-level design docs (unless directly relevant).

### 3. Concrete Over Abstract
Bad: "Improve error handling in the API layer."
Good: "Add try-catch blocks to all route handlers in `src/routes/users.ts`. Catch errors, log them with the existing `logger.error()`, and return a JSON response `{ error: string, code: number }` with appropriate HTTP status codes."

### 4. Boundary Enforcement
Explicitly tell the agent what NOT to touch. This prevents well-meaning agents from "helpfully" refactoring adjacent code.

### 5. Upstream Handoff Format
When a task depends on prior output, include the upstream deliverable directly. Don't say "Task 2 created a file" — paste the file contents or the key interface/type definitions the downstream agent needs.

## Examples

### Example 1: Implementation Agent

```
## Role
You are a Backend Engineer implementing a new API endpoint.

## Context
The application is a REST API built with Express + TypeScript. We are adding user profile photo upload functionality. The storage layer (S3 upload utility) already exists at `src/utils/s3.ts`.

## Task
Create a new route handler for `POST /api/users/:id/photo` that accepts a multipart file upload, validates it (JPEG/PNG only, max 5MB), uploads to S3 via the existing utility, and updates the user record with the new photo URL.

## Input
### Files to read:
- `src/utils/s3.ts` — existing S3 upload utility, use `uploadFile(buffer, key): Promise<string>`
- `src/models/user.ts` — User model, has `photoUrl: string` field
- `src/routes/users.ts` — existing user routes, add the new route here
- `src/middleware/auth.ts` — use `requireAuth` middleware

## Deliverable
- Modify: `src/routes/users.ts` — add the new POST route
- Create: `src/middleware/upload.ts` — multer config for single file upload with validation

## Constraints
- Use multer for multipart parsing
- Follow existing route patterns in users.ts (error format, response shape)
- Do not modify s3.ts, user.ts, or auth.ts

## Done When
- [ ] POST /api/users/:id/photo accepts JPEG/PNG uploads up to 5MB
- [ ] Invalid file types return 400 with descriptive error
- [ ] Oversized files return 400 with descriptive error
- [ ] Successful upload returns 200 with `{ photoUrl: string }`
- [ ] User record is updated with new photoUrl
```

### Example 2: Test Agent

```
## Role
You are a Test Engineer writing integration tests.

## Context
A new photo upload endpoint was just added to the users API. You need to verify it works correctly and handles edge cases.

## Input
### Upstream output (implementation):
[Paste the route handler code and upload middleware created by the implementation agent]

### Files to read:
- `src/tests/helpers.ts` — test utilities (createTestUser, getAuthToken, etc.)
- `src/tests/users.test.ts` — existing user tests, follow the same patterns

## Task
Write integration tests for the `POST /api/users/:id/photo` endpoint covering: successful upload, invalid file type, oversized file, unauthenticated request, and uploading for a non-existent user.

## Deliverable
- Create: `src/tests/users-photo.test.ts`

## Constraints
- Use the existing test framework (Jest + Supertest) as seen in users.test.ts
- Use test helpers from helpers.ts
- Mock S3 uploads (don't hit real S3)

## Done When
- [ ] 5 test cases covering the scenarios listed above
- [ ] All tests are runnable with `npm test`
- [ ] S3 is properly mocked
```

### Example 3: Documentation Agent

```
## Role
You are a Technical Writer updating API documentation.

## Context
A new endpoint for user photo uploads has been added to the REST API.

## Input
### Upstream output:
- Route: POST /api/users/:id/photo
- Auth: Bearer token required
- Body: multipart/form-data with `photo` field
- Accepts: JPEG, PNG, max 5MB
- Success response: `{ photoUrl: string }` (200)
- Error responses: 400 (invalid file), 401 (unauthorized), 404 (user not found)

### Files to read:
- `docs/api.md` — existing API documentation, follow its format exactly

## Task
Add documentation for the new photo upload endpoint to the API docs, following the existing format.

## Deliverable
- Modify: `docs/api.md` — add new endpoint section under "Users"

## Constraints
- Match the heading style, request/response format, and example patterns in the existing doc
- Include a curl example

## Done When
- [ ] New endpoint is documented with description, auth requirements, request format, and all response codes
- [ ] curl example is included
- [ ] Format matches existing documentation style
```
