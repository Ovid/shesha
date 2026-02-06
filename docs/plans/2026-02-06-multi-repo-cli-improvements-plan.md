# Multi-Repo CLI Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `--prd <path>` argument and interactive repo picker to `examples/multi_repo.py`.

**Architecture:** The script gets two new functions (`show_multi_picker` for multi-select repo picking across both storages, and PRD file reading via `--prd`). The argparse config changes to make `repos` optional. No changes to `src/shesha/` — all changes are in `examples/multi_repo.py` and its test file.

**Tech Stack:** Python stdlib (argparse, json, pathlib), existing Shesha API (`list_projects`, `get_project_info`)

---

### Task 1: Make `repos` optional and add `--prd` argument

**Files:**
- Modify: `examples/multi_repo.py:38-51` (parse_args)
- Test: `tests/examples/test_multi_repo.py`

**Step 1: Write the failing tests**

Add to `tests/examples/test_multi_repo.py`:

```python
"""Tests for multi_repo example script."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add examples to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples"))


def test_multi_repo_script_importable():
    """multi_repo.py can be imported."""
    import multi_repo

    assert hasattr(multi_repo, "main")


def test_multi_repo_has_parse_args():
    """multi_repo.py has argument parser."""
    import multi_repo

    assert hasattr(multi_repo, "parse_args")


class TestParseArgs:
    """Tests for parse_args function."""

    def test_repos_optional(self) -> None:
        """No args should work (for picker mode)."""
        from multi_repo import parse_args

        args = parse_args([])
        assert args.repos == []
        assert args.prd is None

    def test_repos_positional(self) -> None:
        """Repo URLs captured as positional args."""
        from multi_repo import parse_args

        args = parse_args(["https://github.com/org/a", "https://github.com/org/b"])
        assert args.repos == ["https://github.com/org/a", "https://github.com/org/b"]

    def test_prd_flag(self) -> None:
        """--prd flag captures file path."""
        from multi_repo import parse_args

        args = parse_args(["--prd", "spec.md"])
        assert args.prd == "spec.md"

    def test_prd_with_repos(self) -> None:
        """--prd works together with repos."""
        from multi_repo import parse_args

        args = parse_args(["repo1", "repo2", "--prd", "spec.md"])
        assert args.repos == ["repo1", "repo2"]
        assert args.prd == "spec.md"

    def test_verbose_flag(self) -> None:
        """--verbose flag should be captured."""
        from multi_repo import parse_args

        args = parse_args(["--verbose"])
        assert args.verbose
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/examples/test_multi_repo.py -v`
Expected: FAIL — `test_repos_optional` fails because `repos` is `nargs="+"` (requires at least 1), and `test_prd_flag` fails because `--prd` doesn't exist.

**Step 3: Write minimal implementation**

In `examples/multi_repo.py`, replace the `parse_args` function:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze PRD impact across multiple repositories")
    parser.add_argument(
        "repos",
        nargs="*",
        help="Git repository URLs or local paths to analyze (shows picker if omitted)",
    )
    parser.add_argument(
        "--prd",
        help="Path to PRD markdown file (prompts for paste if omitted)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress during analysis",
    )
    return parser.parse_args(argv)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/examples/test_multi_repo.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/multi_repo.py tests/examples/test_multi_repo.py
git commit -m "feat(multi-repo): make repos optional and add --prd argument"
```

---

### Task 2: Add PRD file reading in `main()`

**Files:**
- Modify: `examples/multi_repo.py:68-112` (main, PRD section)
- Test: `tests/examples/test_multi_repo.py`

**Step 1: Write the failing tests**

```python
class TestReadPrd:
    """Tests for PRD reading logic."""

    def test_read_prd_from_file(self, tmp_path: Path) -> None:
        """--prd reads content from file."""
        from multi_repo import read_prd

        prd_file = tmp_path / "spec.md"
        prd_file.write_text("# Requirements\n\nDo the thing.")
        result = read_prd(str(prd_file))
        assert result == "# Requirements\n\nDo the thing."

    def test_read_prd_file_not_found(self) -> None:
        """--prd with non-existent file raises SystemExit."""
        from multi_repo import read_prd

        with pytest.raises(SystemExit):
            read_prd("/nonexistent/path.md")

    def test_read_prd_none_falls_back_to_stdin(self) -> None:
        """No --prd prompts for stdin input."""
        from multi_repo import read_prd

        with patch("multi_repo.read_multiline_input", return_value="PRD from stdin"):
            result = read_prd(None)
        assert result == "PRD from stdin"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/examples/test_multi_repo.py::TestReadPrd -v`
Expected: FAIL — `read_prd` doesn't exist.

**Step 3: Write minimal implementation**

Add to `examples/multi_repo.py` after `read_multiline_input`:

```python
def read_prd(prd_path: str | None) -> str:
    """Read PRD from file or stdin.

    Args:
        prd_path: Path to PRD file, or None to read from stdin.

    Returns:
        PRD text content.
    """
    if prd_path is not None:
        path = Path(prd_path)
        if not path.is_file():
            print(f"Error: PRD file not found: {prd_path}")
            sys.exit(1)
        return path.read_text()

    print()
    print("Paste PRD (Ctrl+D or blank line to finish):")
    return read_multiline_input()
```

Then update `main()` to replace the PRD-reading block (lines 105-112) with:

```python
    # Get PRD
    prd = read_prd(args.prd)

    if not prd.strip():
        print("No PRD provided. Exiting.")
        sys.exit(0)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/examples/test_multi_repo.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/multi_repo.py tests/examples/test_multi_repo.py
git commit -m "feat(multi-repo): add read_prd function with file and stdin support"
```

---

### Task 3: Add `collect_repos_from_storages` helper

This function scans both `~/.shesha/multi-repo/` and `~/.shesha/repo-explorer/` and returns a deduplicated list of `(project_id, source_url, storage_label)` tuples.

**Files:**
- Modify: `examples/multi_repo.py`
- Test: `tests/examples/test_multi_repo.py`

**Step 1: Write the failing tests**

```python
class TestCollectReposFromStorages:
    """Tests for collect_repos_from_storages."""

    def test_returns_repos_from_both_storages(self) -> None:
        """Repos from both storages are returned."""
        from multi_repo import collect_repos_from_storages

        mock_multi = MagicMock()
        mock_multi.list_projects.return_value = ["org-auth"]
        mock_multi.get_project_info.return_value = MagicMock(
            project_id="org-auth",
            source_url="https://github.com/org/auth",
            is_local=False,
            source_exists=True,
        )

        mock_explorer = MagicMock()
        mock_explorer.list_projects.return_value = ["org-api"]
        mock_explorer.get_project_info.return_value = MagicMock(
            project_id="org-api",
            source_url="https://github.com/org/api",
            is_local=False,
            source_exists=True,
        )

        repos = collect_repos_from_storages(mock_multi, mock_explorer)
        assert len(repos) == 2
        ids = [r[0] for r in repos]
        assert "org-auth" in ids
        assert "org-api" in ids

    def test_deduplicates_preferring_multi_repo(self) -> None:
        """Same project_id in both storages uses multi-repo copy."""
        from multi_repo import collect_repos_from_storages

        mock_multi = MagicMock()
        mock_multi.list_projects.return_value = ["org-repo"]
        mock_multi.get_project_info.return_value = MagicMock(
            project_id="org-repo",
            source_url="https://github.com/org/repo",
            is_local=False,
            source_exists=True,
        )

        mock_explorer = MagicMock()
        mock_explorer.list_projects.return_value = ["org-repo"]
        mock_explorer.get_project_info.return_value = MagicMock(
            project_id="org-repo",
            source_url="https://github.com/org/repo",
            is_local=False,
            source_exists=True,
        )

        repos = collect_repos_from_storages(mock_multi, mock_explorer)
        assert len(repos) == 1
        assert repos[0][2] == "multi-repo"

    def test_empty_storages(self) -> None:
        """No repos in either storage returns empty list."""
        from multi_repo import collect_repos_from_storages

        mock_multi = MagicMock()
        mock_multi.list_projects.return_value = []

        mock_explorer = MagicMock()
        mock_explorer.list_projects.return_value = []

        repos = collect_repos_from_storages(mock_multi, mock_explorer)
        assert repos == []

    def test_explorer_only(self) -> None:
        """Repos only in explorer storage are returned."""
        from multi_repo import collect_repos_from_storages

        mock_multi = MagicMock()
        mock_multi.list_projects.return_value = []

        mock_explorer = MagicMock()
        mock_explorer.list_projects.return_value = ["Ovid-shesha"]
        mock_explorer.get_project_info.return_value = MagicMock(
            project_id="Ovid-shesha",
            source_url="https://github.com/Ovid/shesha/",
            is_local=False,
            source_exists=True,
        )

        repos = collect_repos_from_storages(mock_multi, mock_explorer)
        assert len(repos) == 1
        assert repos[0][0] == "Ovid-shesha"
        assert repos[0][2] == "repo-explorer"
```

Add `from unittest.mock import MagicMock` to the top of the test file imports.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/examples/test_multi_repo.py::TestCollectReposFromStorages -v`
Expected: FAIL — `collect_repos_from_storages` doesn't exist.

**Step 3: Write minimal implementation**

Add to `examples/multi_repo.py`:

```python
EXPLORER_STORAGE_PATH = Path.home() / ".shesha" / "repo-explorer"


def collect_repos_from_storages(
    multi_shesha: Shesha, explorer_shesha: Shesha
) -> list[tuple[str, str | None, str]]:
    """Collect repos from both multi-repo and repo-explorer storages.

    Returns list of (project_id, source_url, storage_label) tuples.
    Multi-repo storage takes priority for deduplication.
    """
    repos: list[tuple[str, str | None, str]] = []
    seen_ids: set[str] = set()

    # Multi-repo storage first (takes priority)
    for project_id in multi_shesha.list_projects():
        info = multi_shesha.get_project_info(project_id)
        repos.append((project_id, info.source_url, "multi-repo"))
        seen_ids.add(project_id)

    # Repo-explorer storage (skip duplicates)
    for project_id in explorer_shesha.list_projects():
        if project_id in seen_ids:
            continue
        info = explorer_shesha.get_project_info(project_id)
        repos.append((project_id, info.source_url, "repo-explorer"))
        seen_ids.add(project_id)

    return repos
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/examples/test_multi_repo.py::TestCollectReposFromStorages -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/multi_repo.py tests/examples/test_multi_repo.py
git commit -m "feat(multi-repo): add collect_repos_from_storages helper"
```

---

### Task 4: Add `show_multi_picker` function

The interactive all-then-deselect multi-select picker.

**Files:**
- Modify: `examples/multi_repo.py`
- Test: `tests/examples/test_multi_repo.py`

**Step 1: Write the failing tests**

```python
class TestShowMultiPicker:
    """Tests for show_multi_picker."""

    def test_all_selected_by_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        """All repos start selected; 'done' returns all."""
        from multi_repo import show_multi_picker

        repos = [
            ("org-auth", "https://github.com/org/auth", "multi-repo"),
            ("org-api", "https://github.com/org/api", "repo-explorer"),
        ]

        with patch("builtins.input", return_value="done"):
            result = show_multi_picker(repos)

        assert len(result) == 2
        assert ("org-auth", "https://github.com/org/auth", "multi-repo") in result
        assert ("org-api", "https://github.com/org/api", "repo-explorer") in result

    def test_toggle_deselects(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Entering a number deselects that repo."""
        from multi_repo import show_multi_picker

        repos = [
            ("org-auth", "https://github.com/org/auth", "multi-repo"),
            ("org-api", "https://github.com/org/api", "repo-explorer"),
        ]

        with patch("builtins.input", side_effect=["2", "done"]):
            result = show_multi_picker(repos)

        assert len(result) == 1
        assert result[0][0] == "org-auth"

    def test_toggle_reselects(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Entering same number twice re-selects."""
        from multi_repo import show_multi_picker

        repos = [
            ("org-auth", "https://github.com/org/auth", "multi-repo"),
            ("org-api", "https://github.com/org/api", "repo-explorer"),
        ]

        with patch("builtins.input", side_effect=["2", "2", "done"]):
            result = show_multi_picker(repos)

        assert len(result) == 2

    def test_add_url(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'a' prompts for URL and adds it."""
        from multi_repo import show_multi_picker

        repos = [("org-auth", "https://github.com/org/auth", "multi-repo")]

        with patch("builtins.input", side_effect=["a", "https://github.com/org/new", "done"]):
            result = show_multi_picker(repos)

        assert len(result) == 2
        added = [r for r in result if r[0] == "https://github.com/org/new"]
        assert len(added) == 1

    def test_deselect_all_shows_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Deselecting all repos and hitting 'done' shows error and re-prompts."""
        from multi_repo import show_multi_picker

        repos = [("org-auth", "https://github.com/org/auth", "multi-repo")]

        with patch("builtins.input", side_effect=["1", "done", "1", "done"]):
            result = show_multi_picker(repos)

        captured = capsys.readouterr()
        assert "At least one repo must be selected" in captured.out
        assert len(result) == 1

    def test_displays_grouped_by_storage(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Repos are displayed grouped by storage label."""
        from multi_repo import show_multi_picker

        repos = [
            ("org-auth", "https://github.com/org/auth", "multi-repo"),
            ("org-api", "https://github.com/org/api", "repo-explorer"),
        ]

        with patch("builtins.input", return_value="done"):
            show_multi_picker(repos)

        captured = capsys.readouterr()
        assert "[multi-repo]" in captured.out
        assert "[repo-explorer]" in captured.out
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/examples/test_multi_repo.py::TestShowMultiPicker -v`
Expected: FAIL — `show_multi_picker` doesn't exist.

**Step 3: Write minimal implementation**

Add to `examples/multi_repo.py`:

```python
def show_multi_picker(
    repos: list[tuple[str, str | None, str]],
) -> list[tuple[str, str | None, str]]:
    """Show interactive multi-select picker for repos.

    All repos start selected. User enters numbers to toggle,
    'a' to add a URL, 'done' to proceed.

    Args:
        repos: List of (project_id, source_url, storage_label) tuples.

    Returns:
        Selected repos as list of (project_id, source_url, storage_label).
        For user-added URLs, project_id is the URL itself and storage_label is "new".
    """
    # Mutable selection state: index -> selected
    selected = {i: True for i in range(len(repos))}
    all_repos = list(repos)  # May grow if user adds URLs

    while True:
        # Display grouped by storage
        print()
        print("Available repositories:")
        storages = {}
        for i, (pid, url, label) in enumerate(all_repos):
            storages.setdefault(label, []).append((i, pid, url))

        num = 0
        index_map: dict[int, int] = {}  # display_num -> all_repos index
        for label in ["multi-repo", "repo-explorer", "new"]:
            if label not in storages:
                continue
            print(f"  [{label}]")
            for repo_idx, pid, url in storages[label]:
                num += 1
                index_map[num] = repo_idx
                marker = "*" if selected.get(repo_idx, True) else " "
                display = pid
                print(f"    {num}. [{marker}] {display}")

        selected_count = sum(1 for s in selected.values() if s)
        print()
        print(f"Selected: {selected_count}/{len(all_repos)}")
        user_input = input("Toggle number, 'a' to add URL, 'done' to proceed: ").strip()

        if user_input.lower() == "done":
            chosen = [all_repos[i] for i, sel in selected.items() if sel]
            if not chosen:
                print("At least one repo must be selected.")
                continue
            return chosen

        if user_input.lower() == "a":
            url = input("Enter repo URL: ").strip()
            if url:
                idx = len(all_repos)
                all_repos.append((url, url, "new"))
                selected[idx] = True
            continue

        try:
            num_input = int(user_input)
            if num_input in index_map:
                repo_idx = index_map[num_input]
                selected[repo_idx] = not selected[repo_idx]
                action = "Selected" if selected[repo_idx] else "Deselected"
                print(f"  {action}: {all_repos[repo_idx][0]}")
            else:
                print(f"Invalid number: {num_input}")
        except ValueError:
            print(f"Unknown command: '{user_input}'")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/examples/test_multi_repo.py::TestShowMultiPicker -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/multi_repo.py tests/examples/test_multi_repo.py
git commit -m "feat(multi-repo): add show_multi_picker with all-then-deselect"
```

---

### Task 5: Wire picker and PRD into `main()`

Connect everything together in the main function.

**Files:**
- Modify: `examples/multi_repo.py:68-103` (main function)
- Test: `tests/examples/test_multi_repo.py`

**Step 1: Write the failing tests**

```python
class TestMainIntegration:
    """Tests for main() wiring."""

    def test_no_args_shows_picker(self) -> None:
        """No CLI args triggers picker."""
        import os
        import sys as sys_mod

        from multi_repo import main

        mock_shesha = MagicMock()
        mock_shesha.list_projects.return_value = ["org-auth"]
        mock_shesha.get_project_info.return_value = MagicMock(
            project_id="org-auth",
            source_url="https://github.com/org/auth",
            is_local=False,
            source_exists=True,
        )

        with patch.object(sys_mod, "argv", ["multi_repo.py"]):
            with patch.dict(os.environ, {"SHESHA_API_KEY": "test-key"}, clear=True):
                with patch("multi_repo.Shesha", return_value=mock_shesha):
                    with patch("multi_repo.SheshaConfig"):
                        with patch("multi_repo.show_multi_picker", return_value=[]) as mock_picker:
                            with patch("multi_repo.collect_repos_from_storages", return_value=[("org-auth", "https://github.com/org/auth", "multi-repo")]):
                                # Picker returns empty -> no repos selected
                                # But show_multi_picker guarantees at least 1, so mock exit
                                mock_picker.return_value = [("org-auth", "https://github.com/org/auth", "multi-repo")]
                                with patch("multi_repo.read_prd", return_value="some prd"):
                                    with patch.object(MagicMock(), "analyze"):
                                        # We just need to verify picker was called
                                        try:
                                            main()
                                        except (SystemExit, Exception):
                                            pass  # May fail downstream; we only care picker was invoked

        mock_picker.assert_called_once()

    def test_prd_flag_reads_file(self, tmp_path: Path) -> None:
        """--prd flag reads PRD from file instead of stdin."""
        import os
        import sys as sys_mod

        from multi_repo import main

        prd_file = tmp_path / "spec.md"
        prd_file.write_text("# The PRD")

        mock_analyzer = MagicMock()
        mock_analyzer.repos = ["org-auth"]
        mock_analyzer.failed_repos = {}

        mock_shesha = MagicMock()

        with patch.object(sys_mod, "argv", ["multi_repo.py", "https://github.com/org/auth", "--prd", str(prd_file)]):
            with patch.dict(os.environ, {"SHESHA_API_KEY": "test-key"}, clear=True):
                with patch("multi_repo.Shesha", return_value=mock_shesha):
                    with patch("multi_repo.SheshaConfig"):
                        with patch("multi_repo.MultiRepoAnalyzer", return_value=mock_analyzer):
                            with patch("multi_repo.read_multiline_input") as mock_stdin:
                                try:
                                    main()
                                except (SystemExit, Exception):
                                    pass  # May fail downstream

        # Stdin should NOT have been called
        mock_stdin.assert_not_called()

    def test_no_api_key_exits(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Missing API key should print error and exit."""
        import os
        import sys as sys_mod

        from multi_repo import main

        with patch.object(sys_mod, "argv", ["multi_repo.py"]):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(SystemExit) as exc_info:
                    main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "SHESHA_API_KEY" in captured.out
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/examples/test_multi_repo.py::TestMainIntegration -v`
Expected: FAIL — `main()` still uses old flow without picker.

**Step 3: Write minimal implementation**

Rewrite the `main()` function in `examples/multi_repo.py`:

```python
def main() -> None:
    """Main entry point."""
    args = parse_args()

    if not os.environ.get("SHESHA_API_KEY"):
        print("Error: SHESHA_API_KEY environment variable not set.")
        sys.exit(1)

    config = SheshaConfig.load(storage_path=STORAGE_PATH)
    shesha = Shesha(config=config)

    analyzer = MultiRepoAnalyzer(shesha)

    # Determine repos
    if args.repos:
        # Repos provided as CLI args
        repo_urls = args.repos
    else:
        # Interactive picker
        explorer_config = SheshaConfig.load(storage_path=EXPLORER_STORAGE_PATH)
        explorer_shesha = Shesha(config=explorer_config)
        available = collect_repos_from_storages(shesha, explorer_shesha)

        if not available:
            print("No repositories indexed yet.")
            url = input("Enter repo URL or local path: ").strip()
            if not url:
                print("No repository specified. Exiting.")
                sys.exit(0)
            repo_urls = [url]
        else:
            selected = show_multi_picker(available)
            # For multi-repo repos, use project_id; for others, use source_url
            repo_urls = []
            for project_id, source_url, storage_label in selected:
                if storage_label == "multi-repo":
                    repo_urls.append(source_url or project_id)
                else:
                    repo_urls.append(source_url or project_id)

    # Add repos
    for url in repo_urls:
        print(f"Adding: {url}")
        project_id = analyzer.add_repo(url)
        if project_id:
            print(f"  -> {project_id}")
        else:
            print("  Warning: Failed to add (will continue with other repos)")

    # Check if any repos were added successfully
    if not analyzer.repos:
        print("\nError: No repositories could be added.")
        if analyzer.failed_repos:
            print("Failed repos:")
            for url in analyzer.failed_repos:
                print(f"  - {url}")
        sys.exit(1)

    # Warn about partial failures
    if analyzer.failed_repos:
        failed = len(analyzer.failed_repos)
        succeeded = len(analyzer.repos)
        print(f"\nNote: {failed} repo(s) failed, continuing with {succeeded}.")

    # Get PRD
    prd = read_prd(args.prd)

    if not prd.strip():
        print("No PRD provided. Exiting.")
        sys.exit(0)

    # Callbacks (unchanged from current implementation)
    def on_discovery(repo_hint: str) -> str | None:
        """Prompt user to provide URL for discovered dependency."""
        print(f"\nDiscovered dependency: {repo_hint}")
        response = input("Enter repo URL to add (or press Enter to skip): ").strip()
        return response if response else None

    def on_alignment_issue(report: AlignmentReport) -> str:
        print(f"\nAlignment score: {report.alignment_score:.0%}")
        if report.gaps:
            print(f"Gaps: {len(report.gaps)}")
            for gap in report.gaps[:3]:
                print(f"  - {gap}")
        if report.scope_creep:
            print(f"Scope creep: {len(report.scope_creep)}")
            for item in report.scope_creep[:3]:
                print(f"  - {item}")
        return input("Action (revise/accept/abort): ").strip().lower()

    def on_progress(phase: str, message: str) -> None:
        if args.verbose:
            print(f"[{phase}] {message}")

    # Run analysis
    print()
    print("Analyzing...")
    hld, alignment = analyzer.analyze(
        prd,
        on_discovery=on_discovery,
        on_alignment_issue=on_alignment_issue,
        on_progress=on_progress,
    )

    # Output
    print()
    print("=" * 60)
    print("DRAFT HIGH-LEVEL DESIGN")
    print("=" * 60)
    print()
    print(hld.raw_hld)

    print()
    print("=" * 60)
    print(f"ALIGNMENT: {alignment.alignment_score:.0%} coverage")
    print(f"Recommendation: {alignment.recommendation}")
    print("=" * 60)

    # Save option
    print()
    if input("Save to file? (y/n): ").lower() == "y":
        filename = input("Filename [hld-draft.md]: ").strip() or "hld-draft.md"
        Path(filename).write_text(hld.raw_hld)
        print(f"Saved to {filename}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/examples/test_multi_repo.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/multi_repo.py tests/examples/test_multi_repo.py
git commit -m "feat(multi-repo): wire picker and --prd into main()"
```

---

### Task 6: Update docstring, usage, and CHANGELOG

**Files:**
- Modify: `examples/multi_repo.py:1-23` (module docstring)
- Modify: `CHANGELOG.md`

**Step 1: Update docstring**

Replace the module docstring in `examples/multi_repo.py`:

```python
"""Multi-repo PRD analysis using federated queries.

This script analyzes how a PRD (Product Requirements Document) impacts
multiple codebases and generates a draft HLD (High-Level Design).

Usage:
    # Interactive picker + paste PRD
    python examples/multi_repo.py

    # Interactive picker + PRD from file
    python examples/multi_repo.py --prd requirements.md

    # Explicit repos + PRD from file
    python examples/multi_repo.py repo1_url repo2_url --prd spec.md

    # Explicit repos + paste PRD
    python examples/multi_repo.py repo1_url repo2_url

Environment Variables:
    SHESHA_API_KEY: Required. API key for your LLM provider.
    SHESHA_MODEL: Optional. Model name (default: claude-sonnet-4-20250514).

Example:
    $ export SHESHA_API_KEY="your-api-key"
    $ python examples/multi_repo.py --prd my-feature.md
"""
```

**Step 2: Update CHANGELOG.md**

Add under `[Unreleased]` → `Added`:

```
- `examples/multi_repo.py`: `--prd <path>` argument to read PRD from file
- `examples/multi_repo.py`: interactive repo picker with all-then-deselect across both storage locations
```

**Step 3: Commit**

```bash
git add examples/multi_repo.py CHANGELOG.md
git commit -m "docs: update multi_repo.py usage and changelog"
```

---

### Task 7: Run full test suite and lint

**Step 1: Run all tests**

Run: `pytest -v`
Expected: All 562+ tests pass.

**Step 2: Run lint and type check**

Run: `ruff check src tests examples && ruff format --check src tests examples && mypy src/shesha`
Expected: No errors.

**Step 3: Fix any issues found, commit if needed**

```bash
git add -A
git commit -m "fix: address lint/type issues from multi-repo CLI changes"
```
