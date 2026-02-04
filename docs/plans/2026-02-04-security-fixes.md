# Security Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix host-side DoS vulnerabilities in container communication and path traversal issues in repo ingestion and storage.

**Architecture:** Add protocol limits (max buffer, max line, overall deadline) to `ContainerExecutor._read_line()`, and apply `safe_path()` consistently to all filesystem operations in `RepoIngester`.

**Tech Stack:** Python 3.11+, pytest, Docker SDK

---

## Task 1: Add ProtocolError Exception

**Files:**
- Modify: `src/shesha/sandbox/executor.py:1-15`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
class TestProtocolError:
    """Tests for ProtocolError exception."""

    def test_protocol_error_exists(self):
        """ProtocolError is importable from executor module."""
        from shesha.sandbox.executor import ProtocolError

        err = ProtocolError("test message")
        assert str(err) == "test message"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestProtocolError::test_protocol_error_exists -v`
Expected: FAIL with "cannot import name 'ProtocolError'"

**Step 3: Write minimal implementation**

Add to `src/shesha/sandbox/executor.py` after the imports (around line 13):

```python
class ProtocolError(Exception):
    """Container protocol violation (oversized data, timeout)."""

    pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestProtocolError::test_protocol_error_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): add ProtocolError exception for protocol violations"
```

---

## Task 2: Add Protocol Limit Constants

**Files:**
- Modify: `src/shesha/sandbox/executor.py:13-20`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
class TestProtocolLimits:
    """Tests for protocol limit constants."""

    def test_max_buffer_size_exists(self):
        """MAX_BUFFER_SIZE constant is defined."""
        from shesha.sandbox.executor import MAX_BUFFER_SIZE

        assert MAX_BUFFER_SIZE == 10 * 1024 * 1024  # 10 MB

    def test_max_line_length_exists(self):
        """MAX_LINE_LENGTH constant is defined."""
        from shesha.sandbox.executor import MAX_LINE_LENGTH

        assert MAX_LINE_LENGTH == 1 * 1024 * 1024  # 1 MB

    def test_max_read_duration_exists(self):
        """MAX_READ_DURATION constant is defined."""
        from shesha.sandbox.executor import MAX_READ_DURATION

        assert MAX_READ_DURATION == 300  # 5 minutes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestProtocolLimits -v`
Expected: FAIL with "cannot import name 'MAX_BUFFER_SIZE'"

**Step 3: Write minimal implementation**

Add to `src/shesha/sandbox/executor.py` after ProtocolError class:

```python
# Protocol limits to prevent DoS attacks from malicious containers
MAX_BUFFER_SIZE = 10 * 1024 * 1024  # 10 MB max buffer
MAX_LINE_LENGTH = 1 * 1024 * 1024  # 1 MB max single line
MAX_READ_DURATION = 300  # 5 min total deadline
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestProtocolLimits -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): add protocol limit constants for DoS prevention"
```

---

## Task 3: Add Buffer Size Limit to _read_line

**Files:**
- Modify: `src/shesha/sandbox/executor.py:_read_line()`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
class TestBufferLimits:
    """Tests for buffer size limits in _read_line."""

    def test_read_line_raises_on_buffer_overflow(self):
        """_read_line raises ProtocolError when buffer exceeds MAX_BUFFER_SIZE."""
        from shesha.sandbox.executor import (
            ContainerExecutor,
            MAX_BUFFER_SIZE,
            ProtocolError,
        )

        mock_socket = MagicMock()
        # Send chunks that exceed MAX_BUFFER_SIZE without a newline
        chunk_size = 1024 * 1024  # 1 MB chunks
        chunks_needed = (MAX_BUFFER_SIZE // chunk_size) + 2

        chunk_data = [b"x" * chunk_size for _ in range(chunks_needed)]
        chunk_iter = iter(chunk_data)

        def mock_recv(size):
            try:
                return next(chunk_iter)
            except StopIteration:
                return b""

        mock_socket._sock.recv = mock_recv
        mock_socket._sock.settimeout = MagicMock()

        executor = ContainerExecutor()
        executor._socket = mock_socket
        executor._raw_buffer = b""
        executor._content_buffer = b""

        with pytest.raises(ProtocolError) as exc_info:
            executor._read_line(timeout=5)

        assert "buffer" in str(exc_info.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestBufferLimits::test_read_line_raises_on_buffer_overflow -v`
Expected: FAIL (no ProtocolError raised, or test times out)

**Step 3: Write minimal implementation**

Modify `_read_line()` in `src/shesha/sandbox/executor.py`. Add buffer checks after each append to `_raw_buffer` and `_content_buffer`. The method needs these checks:

1. After `self._raw_buffer += chunk` (around lines 205, 217, 238), add:
```python
if len(self._raw_buffer) > MAX_BUFFER_SIZE:
    raise ProtocolError(f"Raw buffer exceeded {MAX_BUFFER_SIZE} bytes")
```

2. After `self._content_buffer += payload` (line 224) and `self._content_buffer += self._raw_buffer` (line 228), add:
```python
if len(self._content_buffer) > MAX_BUFFER_SIZE:
    raise ProtocolError(f"Content buffer exceeded {MAX_BUFFER_SIZE} bytes")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestBufferLimits::test_read_line_raises_on_buffer_overflow -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): add buffer size limits to _read_line"
```

---

## Task 4: Add Overall Deadline to _read_line

**Files:**
- Modify: `src/shesha/sandbox/executor.py:_read_line()`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
import time


class TestReadDeadline:
    """Tests for overall deadline in _read_line."""

    def test_read_line_raises_on_deadline_exceeded(self):
        """_read_line raises ProtocolError when total time exceeds MAX_READ_DURATION."""
        from shesha.sandbox.executor import ContainerExecutor, ProtocolError

        mock_socket = MagicMock()

        # Simulate slow drip that would exceed deadline
        call_count = 0

        def mock_recv(size):
            nonlocal call_count
            call_count += 1
            # Return small chunks without newline
            if call_count < 100:
                return b"x"
            return b""

        mock_socket._sock.recv = mock_recv
        mock_socket._sock.settimeout = MagicMock()

        executor = ContainerExecutor()
        executor._socket = mock_socket
        executor._raw_buffer = b""
        executor._content_buffer = b""

        # Patch time.time to simulate elapsed time exceeding deadline
        start_time = time.time()
        call_sequence = [start_time, start_time + 301]  # 301 seconds elapsed
        time_iter = iter(call_sequence)

        def mock_time():
            try:
                return next(time_iter)
            except StopIteration:
                return start_time + 400

        with patch("shesha.sandbox.executor.time.time", mock_time):
            with pytest.raises(ProtocolError) as exc_info:
                executor._read_line(timeout=5)

        assert "deadline" in str(exc_info.value).lower() or "duration" in str(exc_info.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestReadDeadline::test_read_line_raises_on_deadline_exceeded -v`
Expected: FAIL (no ProtocolError raised)

**Step 3: Write minimal implementation**

Modify `_read_line()` in `src/shesha/sandbox/executor.py`:

1. Add `import time` at the top of the file if not present.

2. At the start of `_read_line()`, add:
```python
start_time = time.time()
```

3. At the start of the `while True:` loop, add:
```python
if time.time() - start_time > MAX_READ_DURATION:
    raise ProtocolError(f"Read duration exceeded {MAX_READ_DURATION} seconds")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestReadDeadline::test_read_line_raises_on_deadline_exceeded -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): add overall deadline to _read_line"
```

---

## Task 5: Add Line Length Limit

**Files:**
- Modify: `src/shesha/sandbox/executor.py:_read_line()`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
class TestLineLengthLimit:
    """Tests for line length limit in _read_line."""

    def test_read_line_raises_on_oversized_line(self):
        """_read_line raises ProtocolError when line exceeds MAX_LINE_LENGTH."""
        from shesha.sandbox.executor import (
            ContainerExecutor,
            MAX_LINE_LENGTH,
            ProtocolError,
        )

        mock_socket = MagicMock()

        # Create a line that exceeds MAX_LINE_LENGTH
        oversized_line = b"x" * (MAX_LINE_LENGTH + 100) + b"\n"
        frame = make_docker_frame(oversized_line)

        chunks = [frame]
        chunk_iter = iter(chunks)

        def mock_recv(size):
            try:
                return next(chunk_iter)
            except StopIteration:
                return b""

        mock_socket._sock.recv = mock_recv
        mock_socket._sock.settimeout = MagicMock()

        executor = ContainerExecutor()
        executor._socket = mock_socket
        executor._raw_buffer = b""
        executor._content_buffer = b""

        with pytest.raises(ProtocolError) as exc_info:
            executor._read_line(timeout=5)

        assert "line" in str(exc_info.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestLineLengthLimit::test_read_line_raises_on_oversized_line -v`
Expected: FAIL (returns the oversized line instead of raising)

**Step 3: Write minimal implementation**

Modify `_read_line()` in `src/shesha/sandbox/executor.py`. Before each `return line.decode()...` or `return result`, add a length check:

```python
# Before returning a line, check its length
if len(line) > MAX_LINE_LENGTH:
    raise ProtocolError(f"Line length {len(line)} exceeds maximum {MAX_LINE_LENGTH}")
```

Apply this check at:
- Line ~182: before `return line.decode().strip()`
- Line ~202-204: before `return result`
- Line ~235-237: before `return result`

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestLineLengthLimit::test_read_line_raises_on_oversized_line -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): add line length limit to _read_line"
```

---

## Task 6: Handle ProtocolError in execute()

**Files:**
- Modify: `src/shesha/sandbox/executor.py:execute()`
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Write the failing test**

Add to `tests/unit/sandbox/test_executor.py`:

```python
class TestExecuteProtocolHandling:
    """Tests for ProtocolError handling in execute()."""

    def test_execute_returns_error_result_on_protocol_error(self):
        """execute() returns error ExecutionResult when ProtocolError occurs."""
        from shesha.sandbox.executor import ContainerExecutor, ProtocolError

        executor = ContainerExecutor()
        executor._socket = MagicMock()

        # Mock _read_line to raise ProtocolError
        with patch.object(executor, "_read_line", side_effect=ProtocolError("buffer overflow")):
            with patch.object(executor, "_send_raw"):
                result = executor.execute("print('hello')")

        assert result.status == "error"
        assert "protocol" in result.error.lower() or "buffer" in result.error.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/sandbox/test_executor.py::TestExecuteProtocolHandling::test_execute_returns_error_result_on_protocol_error -v`
Expected: FAIL (ProtocolError propagates instead of returning ExecutionResult)

**Step 3: Write minimal implementation**

Modify `execute()` in `src/shesha/sandbox/executor.py`. Wrap the while loop in try/except:

```python
def execute(self, code: str, timeout: int = 30) -> ExecutionResult:
    """Execute code in the container, handling llm_query callbacks."""
    self._send_raw(json.dumps({"action": "execute", "code": code}) + "\n")

    try:
        # Handle responses, which may include llm_query requests
        while True:
            # ... existing code ...
    except ProtocolError as e:
        return ExecutionResult(
            status="error",
            stdout="",
            stderr="",
            return_value=None,
            error=f"Protocol error: {e}",
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/sandbox/test_executor.py::TestExecuteProtocolHandling::test_execute_returns_error_result_on_protocol_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/sandbox/test_executor.py src/shesha/sandbox/executor.py
git commit -m "feat(sandbox): handle ProtocolError in execute() gracefully"
```

---

## Task 7: Run All Executor Tests

**Files:**
- Test: `tests/unit/sandbox/test_executor.py`

**Step 1: Run all executor tests**

Run: `pytest tests/unit/sandbox/test_executor.py -v`
Expected: All tests PASS

**Step 2: Run full test suite**

Run: `pytest`
Expected: All tests PASS

**Step 3: Commit (if any fixes needed)**

Only if fixes were needed.

---

## Task 8: Add _repo_path Helper to RepoIngester

**Files:**
- Modify: `src/shesha/repo/ingester.py`
- Test: `tests/unit/repo/test_ingester.py`

**Step 1: Write the failing test**

Add to `tests/unit/repo/test_ingester.py`:

```python
from shesha.security.paths import PathTraversalError


class TestPathTraversalProtection:
    """Tests for path traversal protection in RepoIngester."""

    def test_repo_path_helper_exists(self, ingester: RepoIngester):
        """_repo_path helper method exists and returns safe path."""
        path = ingester._repo_path("valid-project")
        assert path == ingester.repos_dir / "valid-project"

    def test_repo_path_blocks_traversal(self, ingester: RepoIngester):
        """_repo_path raises PathTraversalError on traversal attempt."""
        with pytest.raises(PathTraversalError):
            ingester._repo_path("../escape")

    def test_repo_path_blocks_absolute_path(self, ingester: RepoIngester):
        """_repo_path raises PathTraversalError on absolute path."""
        with pytest.raises(PathTraversalError):
            ingester._repo_path("/etc/passwd")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/repo/test_ingester.py::TestPathTraversalProtection -v`
Expected: FAIL with "has no attribute '_repo_path'"

**Step 3: Write minimal implementation**

Add to `src/shesha/repo/ingester.py`:

1. Add import at top:
```python
from shesha.security.paths import safe_path
```

2. Add helper method after `__init__`:
```python
def _repo_path(self, project_id: str) -> Path:
    """Get safe path for a project's repo directory."""
    return safe_path(self.repos_dir, project_id)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/repo/test_ingester.py::TestPathTraversalProtection -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/repo/test_ingester.py src/shesha/repo/ingester.py
git commit -m "feat(repo): add _repo_path helper with path traversal protection"
```

---

## Task 9: Replace repos_dir / project_id with _repo_path

**Files:**
- Modify: `src/shesha/repo/ingester.py`
- Test: `tests/unit/repo/test_ingester.py`

**Step 1: Write the failing test**

Add to `tests/unit/repo/test_ingester.py` in `TestPathTraversalProtection`:

```python
    def test_clone_blocks_traversal(self, ingester: RepoIngester):
        """clone() raises PathTraversalError on traversal attempt."""
        with pytest.raises(PathTraversalError):
            ingester.clone("https://github.com/org/repo", "../escape")

    def test_save_sha_blocks_traversal(self, ingester: RepoIngester):
        """save_sha() raises PathTraversalError on traversal attempt."""
        with pytest.raises(PathTraversalError):
            ingester.save_sha("../escape", "abc123")

    def test_delete_repo_blocks_traversal(self, ingester: RepoIngester):
        """delete_repo() raises PathTraversalError on traversal attempt."""
        with pytest.raises(PathTraversalError):
            ingester.delete_repo("../escape")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/repo/test_ingester.py::TestPathTraversalProtection -v`
Expected: Some tests FAIL (no PathTraversalError raised)

**Step 3: Write minimal implementation**

Replace all occurrences of `self.repos_dir / project_id` with `self._repo_path(project_id)` in `src/shesha/repo/ingester.py`:

- Line 73: `repo_path = self.repos_dir / project_id` → `repo_path = self._repo_path(project_id)`
- Line 103: `repo_path = self.repos_dir / project_id` → `repo_path = self._repo_path(project_id)`
- Line 110: `repo_path = self.repos_dir / project_id` → `repo_path = self._repo_path(project_id)`
- Line 125: `meta_path = self.repos_dir / project_id / "_repo_meta.json"` → `meta_path = self._repo_path(project_id) / "_repo_meta.json"`
- Line 134: Same pattern
- Line 161: Same pattern
- Line 179: Same pattern
- Line 209: Same pattern
- Line 241: Same pattern
- Line 255: Same pattern
- Line 270: Same pattern

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/repo/test_ingester.py::TestPathTraversalProtection -v`
Expected: PASS

**Step 5: Run all ingester tests**

Run: `pytest tests/unit/repo/test_ingester.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add tests/unit/repo/test_ingester.py src/shesha/repo/ingester.py
git commit -m "feat(repo): apply safe_path to all repo path operations"
```

---

## Task 10: Fix Raw File Copy Path Traversal

**Files:**
- Modify: `src/shesha/storage/filesystem.py:88`
- Test: `tests/unit/storage/test_filesystem.py`

**Step 1: Write the failing test**

Add to `tests/unit/storage/test_filesystem.py` in `TestPathTraversalProtection`:

```python
    def test_raw_file_copy_traversal_blocked(self, tmp_path: Path) -> None:
        """Raw file copy with traversal in doc.name is blocked."""
        storage = FilesystemStorage(tmp_path, keep_raw_files=True)
        storage.create_project("test-project")

        # Create a source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")

        doc = ParsedDocument(
            name="../../../escape.txt",
            content="malicious",
            format="txt",
            metadata={},
            char_count=9,
            parse_warnings=[],
        )
        with pytest.raises(PathTraversalError):
            storage.store_document("test-project", doc, raw_path=source_file)

    def test_raw_file_copy_nested_path_works(self, tmp_path: Path) -> None:
        """Raw file copy with nested path (e.g., src/main.py) works."""
        storage = FilesystemStorage(tmp_path, keep_raw_files=True)
        storage.create_project("test-project")

        # Create a source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")

        doc = ParsedDocument(
            name="src/main.py",
            content="code",
            format="py",
            metadata={},
            char_count=4,
            parse_warnings=[],
        )
        # Should not raise - nested paths are valid
        storage.store_document("test-project", doc, raw_path=source_file)

        # Verify file was created in correct nested location
        raw_path = tmp_path / "projects" / "test-project" / "raw" / "src" / "main.py"
        assert raw_path.exists()
        assert raw_path.read_text() == "content"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/storage/test_filesystem.py::TestPathTraversalProtection -v`
Expected: `test_raw_file_copy_traversal_blocked` FAILS (no exception raised), `test_raw_file_copy_nested_path_works` may FAIL (directory not created)

**Step 3: Write minimal implementation**

Modify `store_document()` in `src/shesha/storage/filesystem.py`, around line 88:

```python
# Store raw file if enabled and path provided
if self.keep_raw_files and raw_path is not None:
    raw_dir = self._project_path(project_id) / "raw"
    raw_dir.mkdir(exist_ok=True)
    raw_dest = safe_path(raw_dir, doc.name)
    raw_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw_path, raw_dest)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_filesystem.py::TestPathTraversalProtection -v`
Expected: PASS

**Step 5: Run all storage tests**

Run: `pytest tests/unit/storage/test_filesystem.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add tests/unit/storage/test_filesystem.py src/shesha/storage/filesystem.py
git commit -m "fix(storage): apply safe_path to raw file copy destination"
```

---

## Task 11: Update SECURITY.md

**Files:**
- Modify: `SECURITY.md`

**Step 1: Read current SECURITY.md**

Review the current content.

**Step 2: Update SECURITY.md**

Add after section "### 5. Secret Redaction":

```markdown
### 6. Protocol Limits

The container communication protocol enforces limits to prevent resource exhaustion:

| Limit | Value | Purpose |
|-------|-------|---------|
| Max buffer size | 10 MB | Prevents memory exhaustion from large outputs |
| Max line length | 1 MB | Prevents oversized JSON messages |
| Max read duration | 5 min | Overall deadline prevents hanging |

When limits are exceeded, the container is terminated and an error is returned.
```

Update section "### 4. Path Traversal Protection":

```markdown
### 4. Path Traversal Protection

- **Safe Path Resolution**: All user-provided paths are resolved and validated against base directories
- **Covers All Storage Operations**: Projects, documents, raw files, and repository directories
- **Filename Sanitization**: Removes null bytes, path separators, and leading dots from filenames
- **Escape Detection**: Raises `PathTraversalError` if resolved path escapes the allowed directory
```

**Step 3: Commit**

```bash
git add SECURITY.md
git commit -m "docs: document protocol limits and path traversal coverage"
```

---

## Task 12: Update CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Read current CHANGELOG.md**

Review the current content.

**Step 2: Update CHANGELOG.md**

Add under `## [Unreleased]`:

```markdown
### Fixed

- Host memory exhaustion via unbounded container output buffering
- Execution hanging indefinitely when container drips output without newlines
- Oversized JSON messages from container causing memory/CPU spike
- Path traversal in repository ingestion when project_id contains path separators
- Path traversal in raw file storage when document name contains path separators

### Security

- Added protocol limits for container communication (max buffer 10MB, max line 1MB, deadline 5min)
- Applied `safe_path()` consistently to all filesystem operations in repo ingestion and storage
```

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG with security fixes"
```

---

## Task 13: Final Verification

**Step 1: Run full test suite**

Run: `make all`
Expected: All checks pass (format, lint, typecheck, test)

**Step 2: Review changes**

Run: `git log --oneline -15`
Verify all commits are present.

**Step 3: Done**

All security fixes implemented and verified.
