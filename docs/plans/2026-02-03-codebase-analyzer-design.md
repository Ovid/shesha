# Codebase Analyzer Feature Design

## Overview

Add optional codebase analysis mode to Shesha. Users can point Shesha at a git repo URL (GitHub, GitLab, Bitbucket) or local path, and it clones/reads, ingests, and formats the code with file headers and line numbers. This enables accurate file:line citations in RLM query responses.

## Use Cases

1. **Deep research queries** - "How does authentication flow through the codebase?" with exact file:line citations
2. **Architecture documentation** - "Explain the architecture of this project" with references to specific code locations

## API Surface

```python
# Create a project from a remote git repo
result = shesha.create_project_from_repo(
    url="https://github.com/org/repo",
    name="my-project",  # optional, defaults to repo name
    token="ghp_xxxxx",  # optional, for private repos
    path="packages/core/",  # optional, subdirectory for monorepos
)

# Create from a local git repo
result = shesha.create_project_from_repo(
    url="/path/to/local/repo",
    name="my-project",
)

# Result object
result.project  # The Project instance
result.status   # "created" | "unchanged" | "updates_available"
result.files_ingested  # int

# Query works the same as before
answer = result.project.query("How does authentication work?")

# Updating when changes are available
if result.status == "updates_available":
    result = result.apply_updates()  # Pull and re-ingest
```

### Return Type

```python
class RepoProjectResult:
    project: Project
    status: Literal["created", "unchanged", "updates_available"]
    files_ingested: int

    def apply_updates(self) -> "RepoProjectResult":
        """Pull changes and re-ingest. Only valid when status is 'updates_available'."""
```

### Update Detection

When `create_project_from_repo()` is called for an existing project:
1. Run `git ls-remote <url> HEAD` to get current remote SHA (cheap network call)
2. Compare to stored SHA from last ingestion
3. If SHAs match → return `status="unchanged"`, no work done
4. If SHAs differ → return `status="updates_available"`, user calls `apply_updates()` to proceed

### Authentication Priority

1. Explicit `token` parameter (if provided)
2. Environment variables: `GITHUB_TOKEN`, `GITLAB_TOKEN`, `BITBUCKET_TOKEN` (matched by URL host)
3. System git credentials (SSH keys, credential helpers)

### Branch Selection

Default branch only. No branch/tag/commit parameter.

### Local vs Remote Detection

- If `url` starts with `/` or `~` or is a valid local path → treat as local repo, skip clone
- Otherwise → treat as remote URL, clone to persistent storage

### File Selection

Everything tracked by git is included (`git ls-files`). No filtering or smart defaults - trust the repo's .gitignore.

Optional `path` parameter restricts ingestion to a subdirectory (for monorepos).

### Storage

Cloned repos are persisted in `{storage_path}/repos/{project_id}/` for faster subsequent updates. Not deleted after ingestion.

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

### Files Without Extensions

Files like `Makefile`, `Dockerfile`, `Jenkinsfile`, `.gitignore`:
- Try to parse as text (skip if binary detected)
- Check first line for shebang (`#!/bin/bash`, `#!/usr/bin/env python`) to identify language for metadata

### Encoding Detection

Use `chardet` library to detect file encoding. Fall back to UTF-8 if detection fails.

## Implementation Components

### 1. New `RepoIngester` class

Location: `src/shesha/repo/ingester.py`

Responsibilities:
- Detect local path vs remote URL
- Git clone with auth for remote (token → URL injection, or system git)
- Detect host (github.com, gitlab.com, bitbucket.org) for env var lookup
- Clone to persistent directory (shallow, depth=1)
- Store HEAD SHA for update detection
- Walk tracked files via `git ls-files`
- Support subdirectory filtering via `path` parameter
- For updates: `git fetch` + compare SHAs, `git pull` if applying

### 2. Modified `CodeParser`

Location: `src/shesha/parser/code.py`

Changes:
- Add optional `include_line_numbers: bool` parameter
- Add optional `file_path: str` parameter for the header
- When enabled, format content with header + numbered lines
- Handle files without extensions: try as text, use shebang for language
- Use `chardet` for encoding detection
- Keep backward compatible (defaults to current behavior)

### 3. New method on `Shesha`

Location: `src/shesha/shesha.py`

New method: `create_project_from_repo(url, name=None, token=None, path=None)`
- Checks if project exists and compares SHA for updates
- Creates project if new
- Instantiates `RepoIngester`
- Iterates files, parses each with line numbers enabled
- Stores via existing storage layer
- Returns `RepoProjectResult`

### 4. New `RepoProjectResult` class

Location: `src/shesha/models.py`

Return type for `create_project_from_repo()` with status and `apply_updates()` method.

### No changes needed to

- RLM engine (already receives doc content + doc_names)
- Storage layer (documents are just strings, repos stored separately)
- System prompt (LLM will naturally see the format)

## Error Handling

### Clone failures

- Invalid URL/path → `ValueError` with message explaining expected format
- Auth failure → `AuthenticationError`: "Private repo requires token. Pass `token=` parameter or set GITHUB_TOKEN environment variable."
- Network/timeout → Git's error wrapped in `RepoIngestError`

### File parsing failures

- Binary files → Skip silently
- Encoding errors → Use chardet, skip file with warning if undecodable
- Empty files → Include with just the header

### Large repos

- No hard limit enforced
- RLM handles large content naturally
- Token costs scale with repo size (user's choice)

### Partial failures

- If some files fail to parse, continue with the rest
- Include stats in `RepoProjectResult`: files_ingested, files_skipped, warnings

## Testing Strategy

### Unit tests

- `RepoIngester`: Mock git commands, verify auth token injection, verify SHA storage/comparison
- `CodeParser` with line numbers: Verify format output, line padding, header generation
- Extensionless files: Verify shebang detection
- Encoding: Verify chardet integration
- `Shesha.create_project_from_repo`: Mock ingester, verify project creation and result object

### Integration tests

- Clone a small public repo (or local git repo in test fixtures)
- Verify files ingested with correct paths and line numbers
- Query the project, verify answer cites file:line accurately
- Test update flow: modify fixture repo, verify `updates_available` status

### Auth tests

- Token parameter takes precedence over env var
- Env var detection by host (github.com → GITHUB_TOKEN)
- Clear error message when private repo and no auth

### Edge cases

- Repo with no code files (just README) → Works, README gets line numbers
- Repo with deeply nested paths → Full paths preserved
- File with 10,000+ lines → Line number padding adjusts correctly
- Local repo path → Works without network
- Subdirectory path → Only files in that path ingested
- Extensionless files with shebang → Language detected correctly
- Calling create_project_from_repo twice with no changes → Returns "unchanged"
