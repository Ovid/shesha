# Multi-Repo CLI Improvements Design

**Date:** 2026-02-06
**Status:** Draft
**Author:** Brainstorming session

## Overview

Improve `examples/multi_repo.py` with two features:
1. `--prd <path>` argument to read PRD from a file instead of pasting
2. Interactive repo picker with all-then-deselect multi-select

## `--prd` Argument

Accepts a path to a markdown (or any text) file containing the PRD.

```bash
# Explicit repos + explicit PRD
python examples/multi_repo.py repo1 repo2 --prd spec.md

# Picker + explicit PRD
python examples/multi_repo.py --prd spec.md

# Picker + paste PRD (fully interactive)
python examples/multi_repo.py
```

- Validates file exists and is readable before proceeding
- If not provided, falls back to existing stdin paste behavior
- `repos` positional argument becomes optional (currently required); if omitted, picker runs

## Repo Picker

When no repos are passed as CLI args, shows an interactive picker listing repos from both storages (`~/.shesha/multi-repo/` and `~/.shesha/repo-explorer/`).

### Display

```
Available repositories:
  [multi-repo]
    (none indexed yet)
  [repo-explorer]
    1. bamate-v2
    2. Ovid-shesha
    3. Perl5-DBIx-Class
    4. PerlDancer-Dancer2

All repos selected. Enter numbers to toggle off, 'a' to add URL, or 'done':
> 3
  Deselected: Perl5-DBIx-Class

Selected (3): bamate-v2, Ovid-shesha, PerlDancer-Dancer2
> done
```

### Behaviors

- Repos grouped by storage source
- All repos start selected; entering a number toggles off/on
- `a` lets user add a new repo URL not yet indexed
- `done` proceeds with selected set
- For repo-explorer repos, reads `_repo_meta.json` to get source URL, passed to `add_repo()` for indexing into multi-repo storage
- If same repo exists in both storages, appears once (prefers multi-repo copy)
- If no repos exist in either storage, prompts for URLs one at a time (blank to stop)
- If user deselects all repos: error message, re-show picker
- Missing local repos shown as `(missing - /old/path)` like `repo.py` does

### Cross-Storage Strategy

The picker collects source URLs from repo-explorer's metadata. The existing `add_repo()` handles both new and existing repos, so it re-indexes into multi-repo storage automatically. No changes needed to `MultiRepoAnalyzer`.

## Updated Flow

```
1. Validate SHESHA_API_KEY
2. Initialize Shesha
3. Determine repos:
   a. If positional args provided -> use those directly
   b. Else -> show picker (both storages, all-then-deselect)
4. Determine PRD:
   a. If --prd <path> provided -> read file
   b. Else -> paste from stdin (existing behavior)
5. add_repo() each selected repo
6. Run analysis (existing behavior)
7. Output results (existing behavior)
```

## Scope

- Changes only `examples/multi_repo.py`
- No changes to `MultiRepoAnalyzer` or any code under `src/shesha/`
