# Synced from GitHub Issue #2

# [SPEC-FIX] Project must be uvx-ready and self-contained; README commands must use uvx; no hardcoded path arguments

## Problem

The project currently has no `pyproject.toml`, so it cannot be installed or run via `uvx` or `uv run`. The README's Quick Start section shows `python -m viewport_editor /path/to/project/root` — this requires both installation and a hardcoded path argument, neither of which is acceptable. The project must be self-contained and runnable with zero setup beyond `uvx`, and the project root must be determined dynamically from the CWD.

## Requirements

### 1. Create pyproject.toml

Add a PEP 621-compliant `pyproject.toml` at the project root with:

- Project metadata (name: `viewport-editor`, version, description, author, license)
- Build system: `hatchling` or similar (not setuptools)
- Dependencies: `mcp` (the MCP SDK), and any other runtime dependencies
- Entry point: `[project.scripts]` pointing to a main function that starts the MCP server

### 2. Project root from CWD

The server determines its project root from the current working directory at startup via `os.getcwd()`. No command-line arguments, no environment variables. When OpenCode launches `uvx viewport-editor`, the CWD is already the project directory, so this works automatically.

### 3. README Quick Start — use uvx

The OpenCode config:

```jsonc
"mcp": {
    "viewport-editor": {
      "type": "local",
      "command": ["uvx", "viewport-editor"],
      "enabled": true
    }
}
```

For other MCP clients:

```json
{
  "mcpServers": {
    "viewport-editor": {
      "command": "uvx",
      "args": ["viewport-editor"]
    }
  }
}
```

### 4. Self-contained

All dependencies declared in `pyproject.toml`. No pip install steps, no venv activation. `uvx viewport-editor` works immediately from any Python 3.10+ environment with `uv`.

## Success Criteria

| ID | Criterion | Evidence Type |
|----|-----------|---------------|
| SC-1 | `pyproject.toml` exists with valid PEP 621 metadata | structural |
| SC-2 | Entry point defined so `uvx viewport-editor` launches the server | behavioral |
| SC-3 | `uv run viewport-editor` works from the repo checkout directory | behavioral |
| SC-4 | Server uses `os.getcwd()` as project root; no command-line path argument accepted | behavioral |
| SC-5 | README Quick Start shows `uvx viewport-editor` without path arguments | string |
| SC-6 | No `python -m viewport_editor` or hardcoded path references remain in README | string |
| SC-7 | All runtime dependencies declared in `pyproject.toml` | structural |

---

🤖 Co-authored with AI: OpenCode (ollama-cloud/deepseek-v4-flash)