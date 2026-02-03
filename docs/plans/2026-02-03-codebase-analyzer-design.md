# Codebase Analyzer Feature Design

## Overview

Add optional codebase analysis mode to Shesha. Users can point Shesha at a git repo URL (GitHub, GitLab, Bitbucket) and it clones, ingests, and formats the code with file headers and line numbers. This enables accurate file:line citations in RLM query responses.

## Use Cases

1. **Deep research queries** - "How does authentication flow through the codebase?" with exact file:line citations
2. **Architecture documentation** - "Explain the architecture of this project" with references to specific code locations

## API Surface

```python
# Create a project from a git repo
project = shesha.create_project_from_repo(
    url="https://github.com/org/repo",
    name="my-project",  # optional, defaults to repo name
    token="ghp_xxxxx",  # optional, for private repos
)

# Query works the same as before
result = project.query("How does authentication work?")
```

### Authentication Priority

1. Explicit `token` parameter (if provided)
2. Environment variables: `GITHUB_TOKEN`, `GITLAB_TOKEN`, `BITBUCKET_TOKEN` (matched by URL host)
3. System git credentials (SSH keys, credential helpers)

### File Selection

Everything tracked by git is included. No filtering or smart defaults - trust the repo's .gitignore.

### Storage

Cloned repo goes to a temp directory during ingestion. After parsing, only the formatted content is stored. Temp clone is deleted.

## Content Formatting

Code files are formatted with file headers and line numbers:

```
=== FILE: src/shesha/rlm/engine.py ===
   1| """RLM engine implementation."""
   2| import asyncio
   3| from typing import Callable
...
 156| def query(self, documents: list[str], ...):
```

- Line number padding adjusts to file length (4 digits for files up to 9999 lines)
- Full paths preserved relative to repo root (avoids ambiguity)
- Non-code files (README.md, .yaml) get the same treatment
- `doc_names` passed to RLM engine use full paths

## Implementation Components

### 1. New `RepoIngester` class

Location: `src/shesha/repo/ingester.py`

Responsibilities:
- Git clone with auth (token → URL injection, or system git)
- Detect host (github.com, gitlab.com, bitbucket.org) for env var lookup
- Clone to temp directory, shallow (depth=1)
- Walk tracked files via `git ls-files`
- Clean up temp directory after ingestion

### 2. Modified `CodeParser`

Location: `src/shesha/parser/code.py`

Changes:
- Add optional `include_line_numbers: bool` parameter
- Add optional `file_path: str` parameter for the header
- When enabled, format content with header + numbered lines
- Keep backward compatible (defaults to current behavior)

### 3. New method on `Shesha`

Location: `src/shesha/shesha.py`

New method: `create_project_from_repo(url, name=None, token=None)`
- Creates project
- Instantiates `RepoIngester`
- Iterates files, parses each with line numbers enabled
- Stores via existing storage layer

### No changes needed to

- RLM engine (already receives doc content + doc_names)
- Storage layer (documents are just strings)
- System prompt (LLM will naturally see the format)

## Error Handling

### Clone failures

- Invalid URL → `ValueError` with message explaining expected format
- Auth failure → `AuthenticationError`: "Private repo requires token. Pass `token=` parameter or set GITHUB_TOKEN environment variable."
- Network/timeout → Git's error wrapped in `RepoIngestError`

### File parsing failures

- Binary files → Skip silently
- Encoding errors → Try UTF-8, fall back to latin-1, log warning if lossy
- Empty files → Include with just the header

### Large repos

- No hard limit enforced
- RLM handles large content naturally
- Token costs scale with repo size (user's choice)

### Partial failures

- If some files fail to parse, continue with the rest
- Return/log summary: "Ingested 142 files, skipped 3 (binary), 1 warning (encoding)"

## Testing Strategy

### Unit tests

- `RepoIngester`: Mock git commands, verify auth token injection, verify temp cleanup
- `CodeParser` with line numbers: Verify format output, line padding, header generation
- `Shesha.create_project_from_repo`: Mock ingester, verify project creation and storage

### Integration tests

- Clone a small public repo (or local git repo in test fixtures)
- Verify files ingested with correct paths and line numbers
- Query the project, verify answer cites file:line accurately

### Auth tests

- Token parameter takes precedence over env var
- Env var detection by host (github.com → GITHUB_TOKEN)
- Clear error message when private repo and no auth

### Edge cases

- Repo with no code files (just README) → Works, README gets line numbers
- Repo with deeply nested paths → Full paths preserved
- File with 10,000+ lines → Line number padding adjusts correctly
