---
name: opencode-docs
description: Expert knowledge on OpenCode configuration, plugins, ecosystem, and customization. Use this when the user asks about configuring OpenCode, creating plugins, or understanding the ecosystem.
compatibility: opencode
---

# OpenCode Documentation & Ecosystem

This skill provides detailed information about OpenCode's configuration, plugin system, and ecosystem.

## Configuration

OpenCode uses a JSON (or JSONC) configuration file.

### Locations & Precedence

Config files are merged, with later sources overriding earlier ones:

1.  **Remote config** (`.well-known/opencode`) - Organization defaults.
2.  **Global config** (`~/.config/opencode/opencode.json`) - User preferences.
3.  **Custom config** (`OPENCODE_CONFIG` env var) - Custom overrides.
4.  **Project config** (`opencode.json` in project root) - Project-specific settings.
5.  **Inline config** (`OPENCODE_CONFIG_CONTENT` env var).

### Schema Highlights

- **`tui`**: Configure scrolling speed, acceleration, and diff styles.
- **`tools`**: Enable/disable specific tools (e.g., `write: false`).
- **`models`**: Set `model`, `small_model`, and provider-specific options (e.g., `timeout`, `apiKey`).
- **`agents`**: Define custom agents with specific prompts, models, and tools.
- **`permissions`**: Control tool execution policies (e.g., `allow`, `ask`, `deny`).
- **`mcp`**: Configure Model Context Protocol servers.

### Variables

- `{env:VARIABLE_NAME}`: Substitutes environment variables.
- `{file:path/to/file}`: Substitutes file contents (useful for secrets or long instructions).

## Plugins

Plugins extend OpenCode by hooking into events.

### Loading Plugins

- **Local**: Place JS/TS files in `.opencode/plugin/` (project) or `~/.config/opencode/plugin/` (global).
- **NPM**: Add package names to the `plugin` array in `opencode.json`.

### Creating Plugins

A plugin exports a function that returns a hooks object.

```typescript
import type { Plugin } from "@opencode-ai/plugin";

export const MyPlugin: Plugin = async ({ project, client, $, directory }) => {
  return {
    "session.created": async (ctx) => {
      // Handle event
    },
    "tool.execute.before": async (input, output) => {
      // Intercept tool usage
    },
  };
};
```

### Key Events

- **Lifecycle**: `session.created`, `session.updated`, `session.idle`
- **Tools**: `tool.execute.before`, `tool.execute.after`
- **Files**: `file.edited`, `file.watcher.updated`
- **TUI**: `tui.command.execute`, `tui.toast.show`

## Agent Skills

Skills are reusable knowledge packages loaded on-demand.

### Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description)
│   └── Markdown body
├── scripts/ (optional)
├── references/ (optional)
└── assets/ (optional)
```

### Discovery

OpenCode looks for `SKILL.md` in:

- `.opencode/skill/<name>/`
- `~/.config/opencode/skill/<name>/`
- `.claude/skills/<name>/` (compatibility mode)

### Permissions

Control access in `opencode.json`:

```json
"permission": {
  "skill": {
    "opencode-docs": "allow",
    "internal-*": "deny"
  }
}
```

## Ecosystem

### Useful Plugins

- **`opencode-helicone-session`**: Analytics/observability.
- **`opencode-devcontainers`**: Dev container support.
- **`opencode-scheduler`**: Schedule recurring jobs.
- **`opencode-websearch-cited`**: Native web search support.

### Projects

- **`opencode.nvim`**: Neovim integration.
- **`opencode-obsidian`**: Obsidian integration.
