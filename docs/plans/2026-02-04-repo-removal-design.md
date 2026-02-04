# Repo Removal Feature Design

## Overview

Add the ability to remove repositories from the picker in `examples/repo.py`, with full cleanup of both indexed project data and cloned repository data (for remote repos).

## Requirements

- Remove indexed project data when deleting
- For remote repos: also delete cloned repo in `~/.shesha/repos/`
- For local repos: only delete indexed data (never touch the original repo)
- Picker should detect when local repos no longer exist at their original path
- Show missing local repos with a warning, let user decide to remove
- Require confirmation before deletion

## Library API Changes

### New: `ProjectInfo` dataclass

```python
@dataclass
class ProjectInfo:
    project_id: str
    source_url: str | None  # None if project not created from repo
    is_local: bool
    source_exists: bool     # Always True for remote repos
```

### New: `Shesha.get_project_info()`

```python
def get_project_info(self, project_id: str) -> ProjectInfo:
    """Get metadata about a project.

    Returns ProjectInfo with source URL, whether it's local,
    and whether the source still exists (for local repos).
    """
```

### Enhanced: `Shesha.delete_project()`

```python
def delete_project(self, project_id: str, *, cleanup_repo: bool = True) -> None:
    """Delete a project and optionally its cloned repository.

    Args:
        project_id: Project to delete.
        cleanup_repo: If True (default), also removes cloned repo data
                      for remote repositories. Has no effect for projects
                      created from local paths.
    """
```

## Internal Implementation

### `delete_project()` flow:

1. Delete indexed project data via `self._storage.delete_project(project_id)`
2. If `cleanup_repo=True`:
   - Get stored repo URL via `_repo_ingester.get_repo_url(project_id)`
   - If URL exists and is NOT a local path: delete `~/.shesha/repos/<project_id>/`
   - If URL is a local path or doesn't exist: do nothing extra

### `get_project_info()` flow:

1. Read stored repo URL from `_repo_ingester.get_repo_url(project_id)`
2. Determine `is_local` via `_repo_ingester.is_local_path(url)`
3. For local repos, check `Path(url).exists()` to set `source_exists`
4. For remote repos, `source_exists` is always `True`

## Example Script Changes (repo.py)

### Enhanced picker display:

```
Available repositories:
  1. github-org-repo
  2. local-project
  3. old-project (missing - /path/no/longer/exists)

Enter number, 'd3' to delete, or new URL:
```

### Deletion flow:

1. User enters `d<N>` (e.g., `d3`)
2. Get project info to determine confirmation message
3. Show confirmation:
   - Local/missing: "Delete 'X'? This will remove all indexed data. (y/n):"
   - Remote: "Delete 'X'? This will remove indexed data and cloned repository. (y/n):"
4. If confirmed, call `shesha.delete_project(project_id)`
5. Re-display picker with updated list

### Input parsing:

- Number → select existing project
- `d<N>` → trigger deletion flow
- Other text → treat as new URL/path
