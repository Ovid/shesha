# Codebase Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add pre-computed codebase analysis to Shesha repositories that supplements the multi-repo HLD builder's reconnaissance phase.

**Architecture:** Analysis is stored as JSON in project storage (`_analysis.json`). The `Shesha` class gains methods to get/generate/check analysis status. The multi-repo analyzer injects analysis as context during recon. The `repo.py` CLI alerts users about missing/stale analysis and provides commands to view/generate it.

**Tech Stack:** Python dataclasses, JSON storage, existing RLM query infrastructure, pytest for TDD.

---

## Task 1: Add Analysis Data Models

**Files:**
- Modify: `src/shesha/models.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test for AnalysisComponent**

Add to `tests/unit/test_models.py`:

```python
class TestAnalysisComponent:
    """Tests for AnalysisComponent dataclass."""

    def test_analysis_component_required_fields(self):
        """AnalysisComponent stores required fields correctly."""
        from shesha.models import AnalysisComponent

        comp = AnalysisComponent(
            name="Server API",
            path="server/",
            description="FastAPI service for chat",
            apis=[{"type": "rest", "endpoints": ["/api/chat"]}],
            models=["ChatSession", "Message"],
            entry_points=["server/main.py"],
            internal_dependencies=["ai_layer"],
        )

        assert comp.name == "Server API"
        assert comp.path == "server/"
        assert comp.description == "FastAPI service for chat"
        assert comp.apis == [{"type": "rest", "endpoints": ["/api/chat"]}]
        assert comp.models == ["ChatSession", "Message"]
        assert comp.entry_points == ["server/main.py"]
        assert comp.internal_dependencies == ["ai_layer"]

    def test_analysis_component_optional_fields(self):
        """AnalysisComponent has optional auth and data_persistence."""
        from shesha.models import AnalysisComponent

        comp = AnalysisComponent(
            name="Web",
            path="web/",
            description="Frontend",
            apis=[],
            models=[],
            entry_points=[],
            internal_dependencies=[],
            auth="Cognito JWT",
            data_persistence="LocalStorage",
        )

        assert comp.auth == "Cognito JWT"
        assert comp.data_persistence == "LocalStorage"

    def test_analysis_component_defaults_none_for_optional(self):
        """AnalysisComponent defaults optional fields to None."""
        from shesha.models import AnalysisComponent

        comp = AnalysisComponent(
            name="Simple",
            path="simple/",
            description="Simple component",
            apis=[],
            models=[],
            entry_points=[],
            internal_dependencies=[],
        )

        assert comp.auth is None
        assert comp.data_persistence is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::TestAnalysisComponent -v`
Expected: FAIL with "cannot import name 'AnalysisComponent'"

**Step 3: Write minimal implementation**

Add to `src/shesha/models.py`:

```python
@dataclass
class AnalysisComponent:
    """A component within a codebase analysis."""

    name: str
    path: str
    description: str
    apis: list[dict[str, Any]]
    models: list[str]
    entry_points: list[str]
    internal_dependencies: list[str]
    auth: str | None = None
    data_persistence: str | None = None
```

Also add `Any` to the typing imports at the top:

```python
from typing import TYPE_CHECKING, Any, Literal
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::TestAnalysisComponent -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/models.py tests/unit/test_models.py
git commit -m "feat(models): add AnalysisComponent dataclass"
```

---

## Task 2: Add AnalysisExternalDep Model

**Files:**
- Modify: `src/shesha/models.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
class TestAnalysisExternalDep:
    """Tests for AnalysisExternalDep dataclass."""

    def test_external_dep_required_fields(self):
        """AnalysisExternalDep stores required fields correctly."""
        from shesha.models import AnalysisExternalDep

        dep = AnalysisExternalDep(
            name="Amazon Bedrock",
            type="ai_service",
            description="Claude model for agent invocations",
            used_by=["ai_layer"],
        )

        assert dep.name == "Amazon Bedrock"
        assert dep.type == "ai_service"
        assert dep.description == "Claude model for agent invocations"
        assert dep.used_by == ["ai_layer"]

    def test_external_dep_optional_defaults_false(self):
        """AnalysisExternalDep defaults optional to False."""
        from shesha.models import AnalysisExternalDep

        dep = AnalysisExternalDep(
            name="PostgreSQL",
            type="database",
            description="Main database",
            used_by=["server"],
        )

        assert dep.optional is False

    def test_external_dep_optional_true(self):
        """AnalysisExternalDep can set optional to True."""
        from shesha.models import AnalysisExternalDep

        dep = AnalysisExternalDep(
            name="Atlassian API",
            type="external_api",
            description="Jira/Confluence integration",
            used_by=["ai_layer"],
            optional=True,
        )

        assert dep.optional is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::TestAnalysisExternalDep -v`
Expected: FAIL with "cannot import name 'AnalysisExternalDep'"

**Step 3: Write minimal implementation**

Add to `src/shesha/models.py`:

```python
@dataclass
class AnalysisExternalDep:
    """An external dependency in a codebase analysis."""

    name: str
    type: str  # external_api, database, message_queue, ai_service, auth_service, storage
    description: str
    used_by: list[str]
    optional: bool = False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::TestAnalysisExternalDep -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/models.py tests/unit/test_models.py
git commit -m "feat(models): add AnalysisExternalDep dataclass"
```

---

## Task 3: Add RepoAnalysis Model

**Files:**
- Modify: `src/shesha/models.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
class TestRepoAnalysis:
    """Tests for RepoAnalysis dataclass."""

    def test_repo_analysis_all_fields(self):
        """RepoAnalysis stores all fields correctly."""
        from shesha.models import AnalysisComponent, AnalysisExternalDep, RepoAnalysis

        comp = AnalysisComponent(
            name="API",
            path="api/",
            description="REST API",
            apis=[],
            models=[],
            entry_points=[],
            internal_dependencies=[],
        )
        dep = AnalysisExternalDep(
            name="Redis",
            type="database",
            description="Cache",
            used_by=["api"],
        )

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123def456",
            overview="A sample application.",
            components=[comp],
            external_dependencies=[dep],
        )

        assert analysis.version == "1"
        assert analysis.generated_at == "2026-02-06T10:30:00Z"
        assert analysis.head_sha == "abc123def456"
        assert analysis.overview == "A sample application."
        assert len(analysis.components) == 1
        assert analysis.components[0].name == "API"
        assert len(analysis.external_dependencies) == 1
        assert analysis.external_dependencies[0].name == "Redis"

    def test_repo_analysis_default_caveats(self):
        """RepoAnalysis has default caveats message."""
        from shesha.models import RepoAnalysis

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test",
            components=[],
            external_dependencies=[],
        )

        assert "AI" in analysis.caveats
        assert "incorrect" in analysis.caveats

    def test_repo_analysis_custom_caveats(self):
        """RepoAnalysis can have custom caveats."""
        from shesha.models import RepoAnalysis

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test",
            components=[],
            external_dependencies=[],
            caveats="Custom warning.",
        )

        assert analysis.caveats == "Custom warning."
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::TestRepoAnalysis -v`
Expected: FAIL with "cannot import name 'RepoAnalysis'"

**Step 3: Write minimal implementation**

Add to `src/shesha/models.py`:

```python
@dataclass
class RepoAnalysis:
    """Pre-computed codebase analysis for HLD builder optimization."""

    version: str
    generated_at: str
    head_sha: str
    overview: str
    components: list[AnalysisComponent]
    external_dependencies: list[AnalysisExternalDep]
    caveats: str = "This analysis was generated by AI and may be incomplete or incorrect."
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::TestRepoAnalysis -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/models.py tests/unit/test_models.py
git commit -m "feat(models): add RepoAnalysis dataclass"
```

---

## Task 4: Add Analysis Storage to StorageBackend Protocol

**Files:**
- Modify: `src/shesha/storage/base.py`
- Test: `tests/unit/storage/test_base.py`

**Step 1: Write the failing test**

Add to `tests/unit/storage/test_base.py`:

```python
"""Tests for storage backend protocol."""

from typing import Protocol, runtime_checkable

import pytest

from shesha.storage.base import StorageBackend


class TestStorageBackendProtocol:
    """Tests for StorageBackend protocol definition."""

    def test_protocol_has_store_analysis_method(self):
        """StorageBackend protocol includes store_analysis method."""
        assert hasattr(StorageBackend, "store_analysis")

    def test_protocol_has_load_analysis_method(self):
        """StorageBackend protocol includes load_analysis method."""
        assert hasattr(StorageBackend, "load_analysis")

    def test_protocol_has_delete_analysis_method(self):
        """StorageBackend protocol includes delete_analysis method."""
        assert hasattr(StorageBackend, "delete_analysis")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/storage/test_base.py -v`
Expected: FAIL (at least one assertion fails because methods don't exist)

**Step 3: Write minimal implementation**

Add to `src/shesha/storage/base.py`, inside the `StorageBackend` protocol class:

```python
    def store_analysis(self, project_id: str, analysis: "RepoAnalysis") -> None:
        """Store a codebase analysis for a project.

        Args:
            project_id: The project to store the analysis for.
            analysis: The analysis to store.
        """
        ...

    def load_analysis(self, project_id: str) -> "RepoAnalysis | None":
        """Load the codebase analysis for a project.

        Args:
            project_id: The project to load the analysis for.

        Returns:
            The stored analysis, or None if no analysis exists.
        """
        ...

    def delete_analysis(self, project_id: str) -> None:
        """Delete the codebase analysis for a project.

        Args:
            project_id: The project to delete the analysis for.
        """
        ...
```

Also add the import at the top of `base.py`:

```python
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shesha.models import RepoAnalysis
```

Update the existing import line and add TYPE_CHECKING block.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_base.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/storage/base.py tests/unit/storage/test_base.py
git commit -m "feat(storage): add analysis methods to StorageBackend protocol"
```

---

## Task 5: Implement Analysis Storage in FilesystemStorage

**Files:**
- Modify: `src/shesha/storage/filesystem.py`
- Test: `tests/unit/storage/test_filesystem.py`

**Step 1: Write the failing tests**

Add to `tests/unit/storage/test_filesystem.py`:

```python
from shesha.models import AnalysisComponent, AnalysisExternalDep, RepoAnalysis


class TestAnalysisOperations:
    """Tests for analysis CRUD operations."""

    def test_store_and_load_analysis(self, storage: FilesystemStorage):
        """Storing an analysis allows retrieval."""
        storage.create_project("analysis-project")

        comp = AnalysisComponent(
            name="API",
            path="api/",
            description="REST API",
            apis=[{"type": "rest", "endpoints": ["/health"]}],
            models=["User"],
            entry_points=["api/main.py"],
            internal_dependencies=[],
            auth="JWT",
        )
        dep = AnalysisExternalDep(
            name="Redis",
            type="database",
            description="Cache",
            used_by=["api"],
            optional=True,
        )
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="A test application.",
            components=[comp],
            external_dependencies=[dep],
        )

        storage.store_analysis("analysis-project", analysis)
        loaded = storage.load_analysis("analysis-project")

        assert loaded is not None
        assert loaded.version == "1"
        assert loaded.head_sha == "abc123"
        assert loaded.overview == "A test application."
        assert len(loaded.components) == 1
        assert loaded.components[0].name == "API"
        assert loaded.components[0].auth == "JWT"
        assert len(loaded.external_dependencies) == 1
        assert loaded.external_dependencies[0].optional is True

    def test_load_analysis_returns_none_when_missing(self, storage: FilesystemStorage):
        """Loading analysis returns None when no analysis exists."""
        storage.create_project("no-analysis")
        loaded = storage.load_analysis("no-analysis")
        assert loaded is None

    def test_delete_analysis(self, storage: FilesystemStorage):
        """Deleting an analysis removes it."""
        storage.create_project("del-analysis")
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="To delete",
            components=[],
            external_dependencies=[],
        )
        storage.store_analysis("del-analysis", analysis)
        storage.delete_analysis("del-analysis")
        assert storage.load_analysis("del-analysis") is None

    def test_delete_analysis_nonexistent_is_noop(self, storage: FilesystemStorage):
        """Deleting nonexistent analysis doesn't raise."""
        storage.create_project("empty-analysis")
        # Should not raise
        storage.delete_analysis("empty-analysis")

    def test_store_analysis_nonexistent_project_raises(self, storage: FilesystemStorage):
        """Storing analysis to nonexistent project raises."""
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Orphan",
            components=[],
            external_dependencies=[],
        )
        with pytest.raises(ProjectNotFoundError):
            storage.store_analysis("no-such-project", analysis)

    def test_load_analysis_nonexistent_project_raises(self, storage: FilesystemStorage):
        """Loading analysis from nonexistent project raises."""
        with pytest.raises(ProjectNotFoundError):
            storage.load_analysis("no-such-project")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/storage/test_filesystem.py::TestAnalysisOperations -v`
Expected: FAIL with "FilesystemStorage has no attribute 'store_analysis'"

**Step 3: Write minimal implementation**

Add to `src/shesha/storage/filesystem.py`:

First, update the imports at the top:

```python
from shesha.models import (
    AnalysisComponent,
    AnalysisExternalDep,
    ParsedDocument,
    RepoAnalysis,
)
```

Then add these methods to the `FilesystemStorage` class:

```python
    def store_analysis(self, project_id: str, analysis: RepoAnalysis) -> None:
        """Store a codebase analysis for a project."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)

        project_path = self._project_path(project_id)
        analysis_path = project_path / "_analysis.json"

        # Convert to dict for JSON serialization
        data = {
            "version": analysis.version,
            "generated_at": analysis.generated_at,
            "head_sha": analysis.head_sha,
            "overview": analysis.overview,
            "components": [
                {
                    "name": c.name,
                    "path": c.path,
                    "description": c.description,
                    "apis": c.apis,
                    "models": c.models,
                    "entry_points": c.entry_points,
                    "internal_dependencies": c.internal_dependencies,
                    "auth": c.auth,
                    "data_persistence": c.data_persistence,
                }
                for c in analysis.components
            ],
            "external_dependencies": [
                {
                    "name": d.name,
                    "type": d.type,
                    "description": d.description,
                    "used_by": d.used_by,
                    "optional": d.optional,
                }
                for d in analysis.external_dependencies
            ],
            "caveats": analysis.caveats,
        }

        analysis_path.write_text(json.dumps(data, indent=2))

    def load_analysis(self, project_id: str) -> RepoAnalysis | None:
        """Load the codebase analysis for a project."""
        if not self.project_exists(project_id):
            raise ProjectNotFoundError(project_id)

        project_path = self._project_path(project_id)
        analysis_path = project_path / "_analysis.json"

        if not analysis_path.exists():
            return None

        data = json.loads(analysis_path.read_text())

        components = [
            AnalysisComponent(
                name=c["name"],
                path=c["path"],
                description=c["description"],
                apis=c["apis"],
                models=c["models"],
                entry_points=c["entry_points"],
                internal_dependencies=c["internal_dependencies"],
                auth=c.get("auth"),
                data_persistence=c.get("data_persistence"),
            )
            for c in data.get("components", [])
        ]

        external_deps = [
            AnalysisExternalDep(
                name=d["name"],
                type=d["type"],
                description=d["description"],
                used_by=d["used_by"],
                optional=d.get("optional", False),
            )
            for d in data.get("external_dependencies", [])
        ]

        return RepoAnalysis(
            version=data["version"],
            generated_at=data["generated_at"],
            head_sha=data["head_sha"],
            overview=data["overview"],
            components=components,
            external_dependencies=external_deps,
            caveats=data.get(
                "caveats",
                "This analysis was generated by AI and may be incomplete or incorrect.",
            ),
        )

    def delete_analysis(self, project_id: str) -> None:
        """Delete the codebase analysis for a project."""
        if not self.project_exists(project_id):
            return  # Silently ignore nonexistent projects

        project_path = self._project_path(project_id)
        analysis_path = project_path / "_analysis.json"

        if analysis_path.exists():
            analysis_path.unlink()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_filesystem.py::TestAnalysisOperations -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/storage/filesystem.py tests/unit/storage/test_filesystem.py
git commit -m "feat(storage): implement analysis storage in FilesystemStorage"
```

---

## Task 6: Add get_analysis_status to Shesha

**Files:**
- Modify: `src/shesha/shesha.py`
- Test: `tests/unit/test_shesha.py`

**Step 1: Write the failing tests**

Add to `tests/unit/test_shesha.py` (find the appropriate test class or create a new one):

```python
class TestAnalysisStatus:
    """Tests for analysis status checking."""

    def test_get_analysis_status_missing(self, shesha_instance, tmp_path):
        """get_analysis_status returns 'missing' when no analysis exists."""
        # Create a project without analysis
        shesha_instance.create_project("no-analysis-project")
        status = shesha_instance.get_analysis_status("no-analysis-project")
        assert status == "missing"

    def test_get_analysis_status_current(self, shesha_instance, tmp_path):
        """get_analysis_status returns 'current' when analysis matches HEAD."""
        from shesha.models import RepoAnalysis

        # Create project and store analysis with matching SHA
        project = shesha_instance.create_project("current-analysis")

        # We need a repo project for SHA comparison - create a mock scenario
        # For unit test, we'll directly store analysis and mock the SHA lookup
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test",
            components=[],
            external_dependencies=[],
        )
        shesha_instance._storage.store_analysis("current-analysis", analysis)

        # Mock the repo ingester to return matching SHA
        shesha_instance._repo_ingester.save_sha("current-analysis", "abc123")
        shesha_instance._repo_ingester.save_source_url("current-analysis", "/fake/path")

        status = shesha_instance.get_analysis_status("current-analysis")
        assert status == "current"

    def test_get_analysis_status_stale(self, shesha_instance, tmp_path):
        """get_analysis_status returns 'stale' when analysis SHA differs from HEAD."""
        from shesha.models import RepoAnalysis

        shesha_instance.create_project("stale-analysis")

        # Store analysis with old SHA
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="old_sha_123",
            overview="Test",
            components=[],
            external_dependencies=[],
        )
        shesha_instance._storage.store_analysis("stale-analysis", analysis)

        # Save different current SHA
        shesha_instance._repo_ingester.save_sha("stale-analysis", "new_sha_456")
        shesha_instance._repo_ingester.save_source_url("stale-analysis", "/fake/path")

        status = shesha_instance.get_analysis_status("stale-analysis")
        assert status == "stale"

    def test_get_analysis_status_nonexistent_project_raises(self, shesha_instance):
        """get_analysis_status raises for nonexistent project."""
        with pytest.raises(ValueError, match="does not exist"):
            shesha_instance.get_analysis_status("no-such-project")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_shesha.py::TestAnalysisStatus -v`
Expected: FAIL with "Shesha has no attribute 'get_analysis_status'"

**Step 3: Write minimal implementation**

Add to `src/shesha/shesha.py`:

```python
    def get_analysis_status(
        self, project_id: str
    ) -> Literal["current", "stale", "missing"]:
        """Check the status of a project's codebase analysis.

        Args:
            project_id: ID of the project.

        Returns:
            'current' if analysis exists and matches current HEAD SHA.
            'stale' if analysis exists but HEAD SHA has changed.
            'missing' if no analysis exists.

        Raises:
            ValueError: If project doesn't exist.
        """
        if not self._storage.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' does not exist")

        analysis = self._storage.load_analysis(project_id)
        if analysis is None:
            return "missing"

        # Get current HEAD SHA
        current_sha = self._repo_ingester.get_saved_sha(project_id)
        if current_sha is None:
            # No SHA saved means we can't verify - treat as current
            return "current"

        if analysis.head_sha == current_sha:
            return "current"

        return "stale"
```

Also update the imports at the top of `shesha.py` to include `Literal` if not already present.

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_shesha.py::TestAnalysisStatus -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/shesha.py tests/unit/test_shesha.py
git commit -m "feat(shesha): add get_analysis_status method"
```

---

## Task 7: Add get_analysis to Shesha

**Files:**
- Modify: `src/shesha/shesha.py`
- Test: `tests/unit/test_shesha.py`

**Step 1: Write the failing tests**

Add to `tests/unit/test_shesha.py`:

```python
class TestGetAnalysis:
    """Tests for get_analysis method."""

    def test_get_analysis_returns_stored_analysis(self, shesha_instance):
        """get_analysis returns the stored analysis."""
        from shesha.models import AnalysisComponent, RepoAnalysis

        shesha_instance.create_project("get-analysis-project")

        comp = AnalysisComponent(
            name="API",
            path="api/",
            description="REST API",
            apis=[],
            models=["User"],
            entry_points=["main.py"],
            internal_dependencies=[],
        )
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test app",
            components=[comp],
            external_dependencies=[],
        )
        shesha_instance._storage.store_analysis("get-analysis-project", analysis)

        result = shesha_instance.get_analysis("get-analysis-project")

        assert result is not None
        assert result.overview == "Test app"
        assert len(result.components) == 1
        assert result.components[0].name == "API"

    def test_get_analysis_returns_none_when_missing(self, shesha_instance):
        """get_analysis returns None when no analysis exists."""
        shesha_instance.create_project("no-analysis")
        result = shesha_instance.get_analysis("no-analysis")
        assert result is None

    def test_get_analysis_nonexistent_project_raises(self, shesha_instance):
        """get_analysis raises for nonexistent project."""
        with pytest.raises(ValueError, match="does not exist"):
            shesha_instance.get_analysis("no-such-project")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_shesha.py::TestGetAnalysis -v`
Expected: FAIL with "Shesha has no attribute 'get_analysis'"

**Step 3: Write minimal implementation**

Add to `src/shesha/shesha.py`:

```python
    def get_analysis(self, project_id: str) -> "RepoAnalysis | None":
        """Get the codebase analysis for a project.

        Args:
            project_id: ID of the project.

        Returns:
            The stored analysis, or None if no analysis exists.

        Raises:
            ValueError: If project doesn't exist.
        """
        if not self._storage.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' does not exist")

        return self._storage.load_analysis(project_id)
```

Also add the import at the top (in TYPE_CHECKING block):

```python
if TYPE_CHECKING:
    from shesha.models import RepoAnalysis
    from shesha.parser.base import DocumentParser
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_shesha.py::TestGetAnalysis -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/shesha.py tests/unit/test_shesha.py
git commit -m "feat(shesha): add get_analysis method"
```

---

## Task 8: Create Analysis Generator Module Structure

**Files:**
- Create: `src/shesha/analysis/__init__.py`
- Create: `src/shesha/analysis/generator.py`
- Create: `tests/unit/analysis/__init__.py`
- Create: `tests/unit/analysis/test_generator.py`

**Step 1: Create directory structure and init files**

```bash
mkdir -p src/shesha/analysis
mkdir -p tests/unit/analysis
touch src/shesha/analysis/__init__.py
touch tests/unit/analysis/__init__.py
```

**Step 2: Write the failing test for generator structure**

Create `tests/unit/analysis/test_generator.py`:

```python
"""Tests for analysis generator."""

import pytest


class TestAnalysisGeneratorStructure:
    """Tests for AnalysisGenerator class structure."""

    def test_generator_can_be_imported(self):
        """AnalysisGenerator can be imported from shesha.analysis."""
        from shesha.analysis import AnalysisGenerator

        assert AnalysisGenerator is not None

    def test_generator_takes_shesha_instance(self):
        """AnalysisGenerator constructor takes a Shesha instance."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        generator = AnalysisGenerator(mock_shesha)

        assert generator._shesha is mock_shesha
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisGeneratorStructure -v`
Expected: FAIL with "cannot import name 'AnalysisGenerator'"

**Step 4: Write minimal implementation**

Create `src/shesha/analysis/generator.py`:

```python
"""Codebase analysis generator."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shesha import Shesha


class AnalysisGenerator:
    """Generates codebase analysis using RLM queries."""

    def __init__(self, shesha: "Shesha") -> None:
        """Initialize the generator.

        Args:
            shesha: Shesha instance for project access.
        """
        self._shesha = shesha
```

Update `src/shesha/analysis/__init__.py`:

```python
"""Codebase analysis module."""

from shesha.analysis.generator import AnalysisGenerator

__all__ = ["AnalysisGenerator"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisGeneratorStructure -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/shesha/analysis tests/unit/analysis
git commit -m "feat(analysis): create analysis generator module structure"
```

---

## Task 9: Create Analysis Generation Prompt

**Files:**
- Create: `src/shesha/analysis/prompts/generate.md`
- Test: `tests/unit/analysis/test_generator.py`

**Step 1: Write the failing test for prompt loading**

Add to `tests/unit/analysis/test_generator.py`:

```python
class TestAnalysisPromptLoading:
    """Tests for prompt loading."""

    def test_load_prompt_returns_string(self):
        """_load_prompt returns prompt content as string."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        generator = AnalysisGenerator(mock_shesha)

        prompt = generator._load_prompt("generate")

        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should have substantial content

    def test_load_prompt_contains_json_schema(self):
        """_load_prompt for generate contains JSON schema example."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        generator = AnalysisGenerator(mock_shesha)

        prompt = generator._load_prompt("generate")

        assert "overview" in prompt
        assert "components" in prompt
        assert "external_dependencies" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisPromptLoading -v`
Expected: FAIL with "AnalysisGenerator has no attribute '_load_prompt'"

**Step 3: Write minimal implementation**

First create the prompts directory:

```bash
mkdir -p src/shesha/analysis/prompts
```

Create `src/shesha/analysis/prompts/generate.md`:

```markdown
# Codebase Analysis

Analyze this codebase and produce a structured analysis in JSON format. Your goal is to identify the major components, their public APIs, data models, entry points, and external dependencies.

## Instructions

1. Explore the codebase structure to understand the major components/services
2. For each component, identify:
   - Public APIs (REST endpoints, GraphQL operations, gRPC services, CLI commands, event handlers)
   - Key data models and schemas
   - Main entry points (startup files, handlers)
   - Dependencies on other components in the same codebase
   - Authentication mechanisms (if any)
   - Data persistence mechanisms (if any)
3. Identify external dependencies (third-party services, databases, message queues)
4. Write a high-level overview summarizing what this codebase does

## Output Format

Return a JSON object with this structure:

```json
{
  "overview": "A 2-3 sentence summary of what this codebase does and its primary purpose.",
  "components": [
    {
      "name": "Component Name",
      "path": "path/to/component/",
      "description": "What this component does",
      "apis": [
        {
          "type": "rest",
          "endpoints": ["GET /api/users", "POST /api/users"]
        }
      ],
      "models": ["User", "Session"],
      "entry_points": ["path/to/main.py"],
      "internal_dependencies": ["other-component-name"],
      "auth": "Description of auth mechanism or null",
      "data_persistence": "Description of storage or null"
    }
  ],
  "external_dependencies": [
    {
      "name": "Service Name",
      "type": "database|external_api|message_queue|ai_service|auth_service|storage",
      "description": "How this dependency is used",
      "used_by": ["component-name"],
      "optional": false
    }
  ]
}
```

## API Types

Use these types for the `apis` array:
- `rest`: REST API endpoints
- `graphql`: GraphQL queries/mutations
- `grpc`: gRPC service methods
- `cli`: Command-line interface commands
- `events`: Event handlers or message consumers

## Important Notes

- Focus on PUBLIC interfaces that other systems might integrate with
- Include internal component dependencies to show how the system is structured
- Mark external dependencies as `optional: true` if the system can function without them
- Be specific about endpoints and models - list actual names, not placeholders
```

Add the `_load_prompt` method to `src/shesha/analysis/generator.py`:

```python
from pathlib import Path


class AnalysisGenerator:
    """Generates codebase analysis using RLM queries."""

    def __init__(self, shesha: "Shesha") -> None:
        """Initialize the generator.

        Args:
            shesha: Shesha instance for project access.
        """
        self._shesha = shesha

    def _load_prompt(self, name: str) -> str:
        """Load a prompt template from the prompts directory."""
        prompts_dir = Path(__file__).parent / "prompts"
        return (prompts_dir / f"{name}.md").read_text()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisPromptLoading -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/analysis
git commit -m "feat(analysis): add generate prompt and prompt loading"
```

---

## Task 10: Implement generate() Method

**Files:**
- Modify: `src/shesha/analysis/generator.py`
- Test: `tests/unit/analysis/test_generator.py`

**Step 1: Write the failing test**

Add to `tests/unit/analysis/test_generator.py`:

```python
class TestAnalysisGeneration:
    """Tests for generate() method."""

    def test_generate_returns_repo_analysis(self):
        """generate() returns a RepoAnalysis object."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator
        from shesha.models import RepoAnalysis

        # Mock the shesha instance and project
        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_shesha.get_project.return_value = mock_project

        # Mock query result with valid JSON
        mock_result = MagicMock()
        mock_result.answer = '''
        ```json
        {
          "overview": "A test application.",
          "components": [
            {
              "name": "API",
              "path": "api/",
              "description": "REST API",
              "apis": [{"type": "rest", "endpoints": ["/health"]}],
              "models": ["User"],
              "entry_points": ["api/main.py"],
              "internal_dependencies": [],
              "auth": null,
              "data_persistence": null
            }
          ],
          "external_dependencies": []
        }
        ```
        '''
        mock_project.query.return_value = mock_result

        # Mock repo ingester for SHA
        mock_shesha._repo_ingester.get_saved_sha.return_value = "abc123def"

        generator = AnalysisGenerator(mock_shesha)
        result = generator.generate("test-project")

        assert isinstance(result, RepoAnalysis)
        assert result.overview == "A test application."
        assert result.head_sha == "abc123def"
        assert result.version == "1"
        assert len(result.components) == 1
        assert result.components[0].name == "API"

    def test_generate_calls_project_query(self):
        """generate() calls project.query with the generate prompt."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_shesha.get_project.return_value = mock_project

        mock_result = MagicMock()
        mock_result.answer = '{"overview": "Test", "components": [], "external_dependencies": []}'
        mock_project.query.return_value = mock_result
        mock_shesha._repo_ingester.get_saved_sha.return_value = "sha123"

        generator = AnalysisGenerator(mock_shesha)
        generator.generate("test-project")

        mock_shesha.get_project.assert_called_once_with("test-project")
        mock_project.query.assert_called_once()

        # Verify prompt contains expected content
        call_args = mock_project.query.call_args
        prompt = call_args[0][0]
        assert "overview" in prompt
        assert "components" in prompt

    def test_generate_handles_missing_sha(self):
        """generate() handles missing SHA gracefully."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_shesha.get_project.return_value = mock_project

        mock_result = MagicMock()
        mock_result.answer = '{"overview": "Test", "components": [], "external_dependencies": []}'
        mock_project.query.return_value = mock_result
        mock_shesha._repo_ingester.get_saved_sha.return_value = None

        generator = AnalysisGenerator(mock_shesha)
        result = generator.generate("test-project")

        assert result.head_sha == ""  # Empty string when no SHA
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisGeneration -v`
Expected: FAIL with "AnalysisGenerator has no attribute 'generate'"

**Step 3: Write minimal implementation**

Update `src/shesha/analysis/generator.py`:

```python
"""Codebase analysis generator."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shesha.models import (
    AnalysisComponent,
    AnalysisExternalDep,
    RepoAnalysis,
)

if TYPE_CHECKING:
    from shesha import Shesha


class AnalysisGenerator:
    """Generates codebase analysis using RLM queries."""

    def __init__(self, shesha: "Shesha") -> None:
        """Initialize the generator.

        Args:
            shesha: Shesha instance for project access.
        """
        self._shesha = shesha

    def _load_prompt(self, name: str) -> str:
        """Load a prompt template from the prompts directory."""
        prompts_dir = Path(__file__).parent / "prompts"
        return (prompts_dir / f"{name}.md").read_text()

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """Extract JSON object from text that may contain markdown."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        start_idx = text.find("{")
        if start_idx != -1:
            for end_idx in range(len(text) - 1, start_idx, -1):
                if text[end_idx] == "}":
                    candidate = text[start_idx : end_idx + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue

        return None

    def generate(self, project_id: str) -> RepoAnalysis:
        """Generate a codebase analysis for a project.

        Args:
            project_id: The project to analyze.

        Returns:
            RepoAnalysis with the generated analysis.
        """
        project = self._shesha.get_project(project_id)
        prompt = self._load_prompt("generate")

        result = project.query(prompt)
        data = self._extract_json(result.answer)

        if data is None:
            data = {"overview": result.answer, "components": [], "external_dependencies": []}

        # Get current SHA
        head_sha = self._shesha._repo_ingester.get_saved_sha(project_id) or ""

        # Parse components
        components = []
        for c in data.get("components", []):
            components.append(
                AnalysisComponent(
                    name=c.get("name", "Unknown"),
                    path=c.get("path", ""),
                    description=c.get("description", ""),
                    apis=c.get("apis", []),
                    models=c.get("models", []),
                    entry_points=c.get("entry_points", []),
                    internal_dependencies=c.get("internal_dependencies", []),
                    auth=c.get("auth"),
                    data_persistence=c.get("data_persistence"),
                )
            )

        # Parse external dependencies
        external_deps = []
        for d in data.get("external_dependencies", []):
            external_deps.append(
                AnalysisExternalDep(
                    name=d.get("name", "Unknown"),
                    type=d.get("type", "external_api"),
                    description=d.get("description", ""),
                    used_by=d.get("used_by", []),
                    optional=d.get("optional", False),
                )
            )

        return RepoAnalysis(
            version="1",
            generated_at=datetime.now(timezone.utc).isoformat(),
            head_sha=head_sha,
            overview=data.get("overview", ""),
            components=components,
            external_dependencies=external_deps,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/analysis/test_generator.py::TestAnalysisGeneration -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/analysis/generator.py tests/unit/analysis/test_generator.py
git commit -m "feat(analysis): implement generate() method"
```

---

## Task 11: Add generate_analysis to Shesha

**Files:**
- Modify: `src/shesha/shesha.py`
- Test: `tests/unit/test_shesha.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_shesha.py`:

```python
class TestGenerateAnalysis:
    """Tests for generate_analysis method."""

    def test_generate_analysis_stores_result(self, shesha_instance, mocker):
        """generate_analysis stores the generated analysis."""
        from shesha.models import RepoAnalysis

        # Create a project
        shesha_instance.create_project("gen-analysis")
        shesha_instance._repo_ingester.save_sha("gen-analysis", "sha123")

        # Mock the generator
        mock_analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="sha123",
            overview="Generated analysis",
            components=[],
            external_dependencies=[],
        )

        mock_generator = mocker.patch("shesha.shesha.AnalysisGenerator")
        mock_generator.return_value.generate.return_value = mock_analysis

        result = shesha_instance.generate_analysis("gen-analysis")

        assert result.overview == "Generated analysis"
        # Verify it was stored
        stored = shesha_instance._storage.load_analysis("gen-analysis")
        assert stored is not None
        assert stored.overview == "Generated analysis"

    def test_generate_analysis_returns_analysis(self, shesha_instance, mocker):
        """generate_analysis returns the generated RepoAnalysis."""
        from shesha.models import RepoAnalysis

        shesha_instance.create_project("return-analysis")

        mock_analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc",
            overview="Test",
            components=[],
            external_dependencies=[],
        )

        mock_generator = mocker.patch("shesha.shesha.AnalysisGenerator")
        mock_generator.return_value.generate.return_value = mock_analysis

        result = shesha_instance.generate_analysis("return-analysis")

        assert isinstance(result, RepoAnalysis)
        assert result.overview == "Test"

    def test_generate_analysis_nonexistent_project_raises(self, shesha_instance):
        """generate_analysis raises for nonexistent project."""
        with pytest.raises(ValueError, match="does not exist"):
            shesha_instance.generate_analysis("no-such-project")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_shesha.py::TestGenerateAnalysis -v`
Expected: FAIL with "Shesha has no attribute 'generate_analysis'"

**Step 3: Write minimal implementation**

Add to `src/shesha/shesha.py`:

First, add the import at the top:

```python
from shesha.analysis import AnalysisGenerator
```

Then add the method:

```python
    def generate_analysis(self, project_id: str) -> "RepoAnalysis":
        """Generate and store a codebase analysis for a project.

        Args:
            project_id: ID of the project to analyze.

        Returns:
            The generated RepoAnalysis.

        Raises:
            ValueError: If project doesn't exist.
        """
        if not self._storage.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' does not exist")

        generator = AnalysisGenerator(self)
        analysis = generator.generate(project_id)
        self._storage.store_analysis(project_id, analysis)
        return analysis
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_shesha.py::TestGenerateAnalysis -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/shesha.py tests/unit/test_shesha.py
git commit -m "feat(shesha): add generate_analysis method"
```

---

## Task 12: Add analysis_status to ProjectInfo

**Files:**
- Modify: `src/shesha/models.py`
- Modify: `src/shesha/shesha.py`
- Test: `tests/unit/test_models.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_models.py`:

```python
class TestProjectInfoAnalysisStatus:
    """Tests for ProjectInfo.analysis_status field."""

    def test_project_info_with_analysis_status(self):
        """ProjectInfo can include analysis_status."""
        info = ProjectInfo(
            project_id="my-project",
            source_url="https://github.com/org/repo",
            is_local=False,
            source_exists=True,
            analysis_status="current",
        )

        assert info.analysis_status == "current"

    def test_project_info_analysis_status_defaults_none(self):
        """ProjectInfo.analysis_status defaults to None."""
        info = ProjectInfo(
            project_id="my-project",
            source_url=None,
            is_local=False,
            source_exists=True,
        )

        assert info.analysis_status is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::TestProjectInfoAnalysisStatus -v`
Expected: FAIL with "unexpected keyword argument 'analysis_status'"

**Step 3: Write minimal implementation**

Update `src/shesha/models.py`, modify `ProjectInfo`:

```python
@dataclass
class ProjectInfo:
    """Metadata about a project's source."""

    project_id: str
    source_url: str | None
    is_local: bool
    source_exists: bool
    analysis_status: Literal["current", "stale", "missing"] | None = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py::TestProjectInfoAnalysisStatus -v`
Expected: PASS

**Step 5: Update get_project_info to populate analysis_status**

Add test to `tests/unit/test_shesha.py`:

```python
class TestGetProjectInfoWithAnalysis:
    """Tests for get_project_info including analysis_status."""

    def test_get_project_info_includes_analysis_status(self, shesha_instance):
        """get_project_info includes analysis_status field."""
        shesha_instance.create_project("info-with-status")

        info = shesha_instance.get_project_info("info-with-status")

        assert info.analysis_status == "missing"  # No analysis yet

    def test_get_project_info_analysis_status_current(self, shesha_instance):
        """get_project_info shows 'current' when analysis matches SHA."""
        from shesha.models import RepoAnalysis

        shesha_instance.create_project("info-current")
        shesha_instance._repo_ingester.save_sha("info-current", "sha123")
        shesha_instance._repo_ingester.save_source_url("info-current", "/fake")

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="sha123",
            overview="Test",
            components=[],
            external_dependencies=[],
        )
        shesha_instance._storage.store_analysis("info-current", analysis)

        info = shesha_instance.get_project_info("info-current")

        assert info.analysis_status == "current"
```

Update `get_project_info` in `src/shesha/shesha.py`:

```python
    def get_project_info(self, project_id: str) -> ProjectInfo:
        """Get metadata about a project.

        Args:
            project_id: ID of the project.

        Returns:
            ProjectInfo with source URL, whether it's local, source existence,
            and analysis status.

        Raises:
            ValueError: If project doesn't exist.
        """
        if not self._storage.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' does not exist")

        source_url = self._repo_ingester.get_source_url(project_id)

        if source_url is None:
            return ProjectInfo(
                project_id=project_id,
                source_url=None,
                is_local=False,
                source_exists=True,
                analysis_status=self.get_analysis_status(project_id),
            )

        is_local = self._repo_ingester.is_local_path(source_url)

        if is_local:
            source_exists = Path(source_url).expanduser().exists()
        else:
            source_exists = True  # Remote repos always "exist"

        return ProjectInfo(
            project_id=project_id,
            source_url=source_url,
            is_local=is_local,
            source_exists=source_exists,
            analysis_status=self.get_analysis_status(project_id),
        )
```

**Step 6: Run all tests to verify**

Run: `pytest tests/unit/test_models.py::TestProjectInfoAnalysisStatus tests/unit/test_shesha.py::TestGetProjectInfoWithAnalysis -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src/shesha/models.py src/shesha/shesha.py tests/unit/test_models.py tests/unit/test_shesha.py
git commit -m "feat(models): add analysis_status to ProjectInfo"
```

---

## Task 13: Add repo.py Analysis Status Alerts

**Files:**
- Modify: `examples/repo.py`
- Test: `tests/unit/test_repo_script.py`

**Step 1: Write the failing test for is_analysis_command**

Add to `tests/unit/test_script_utils.py`:

```python
class TestAnalysisCommands:
    """Tests for analysis command detection."""

    def test_is_analysis_command_analysis(self):
        """'analysis' is recognized as analysis command."""
        from script_utils import is_analysis_command

        assert is_analysis_command("analysis") is True

    def test_is_analysis_command_show_analysis(self):
        """'show analysis' is recognized as analysis command."""
        from script_utils import is_analysis_command

        assert is_analysis_command("show analysis") is True

    def test_is_analysis_command_case_insensitive(self):
        """Analysis command is case insensitive."""
        from script_utils import is_analysis_command

        assert is_analysis_command("ANALYSIS") is True
        assert is_analysis_command("Analysis") is True

    def test_is_analysis_command_other(self):
        """Other commands are not analysis commands."""
        from script_utils import is_analysis_command

        assert is_analysis_command("help") is False
        assert is_analysis_command("quit") is False


class TestRegenerateCommands:
    """Tests for regenerate command detection."""

    def test_is_regenerate_command_analyze(self):
        """'analyze' is recognized as regenerate command."""
        from script_utils import is_regenerate_command

        assert is_regenerate_command("analyze") is True

    def test_is_regenerate_command_regenerate(self):
        """'regenerate analysis' is recognized as regenerate command."""
        from script_utils import is_regenerate_command

        assert is_regenerate_command("regenerate analysis") is True

    def test_is_regenerate_command_case_insensitive(self):
        """Regenerate command is case insensitive."""
        from script_utils import is_regenerate_command

        assert is_regenerate_command("ANALYZE") is True

    def test_is_regenerate_command_other(self):
        """Other commands are not regenerate commands."""
        from script_utils import is_regenerate_command

        assert is_regenerate_command("analysis") is False
        assert is_regenerate_command("help") is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_script_utils.py::TestAnalysisCommands tests/unit/test_script_utils.py::TestRegenerateCommands -v`
Expected: FAIL with "cannot import name 'is_analysis_command'"

**Step 3: Write minimal implementation**

Add to `examples/script_utils.py`:

```python
def is_analysis_command(text: str) -> bool:
    """Check if text is a command to show analysis."""
    lower = text.lower().strip()
    return lower in ("analysis", "show analysis")


def is_regenerate_command(text: str) -> bool:
    """Check if text is a command to regenerate analysis."""
    lower = text.lower().strip()
    return lower in ("analyze", "regenerate analysis")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_script_utils.py::TestAnalysisCommands tests/unit/test_script_utils.py::TestRegenerateCommands -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/script_utils.py tests/unit/test_script_utils.py
git commit -m "feat(script_utils): add analysis command detection helpers"
```

---

## Task 14: Add format_analysis_for_display

**Files:**
- Modify: `examples/script_utils.py`
- Test: `tests/unit/test_script_utils.py`

**Step 1: Write the failing test**

Add to `tests/unit/test_script_utils.py`:

```python
class TestFormatAnalysisForDisplay:
    """Tests for analysis display formatting."""

    def test_format_analysis_includes_header(self):
        """Formatted analysis includes header with date."""
        from script_utils import format_analysis_for_display

        from shesha.models import RepoAnalysis

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123def456",
            overview="A test application.",
            components=[],
            external_dependencies=[],
        )

        output = format_analysis_for_display(analysis)

        assert "2026-02-06" in output
        assert "abc123de" in output  # First 8 chars of SHA

    def test_format_analysis_includes_overview(self):
        """Formatted analysis includes overview section."""
        from script_utils import format_analysis_for_display

        from shesha.models import RepoAnalysis

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="This is a complex microservices application.",
            components=[],
            external_dependencies=[],
        )

        output = format_analysis_for_display(analysis)

        assert "Overview" in output
        assert "This is a complex microservices application." in output

    def test_format_analysis_includes_components(self):
        """Formatted analysis includes components."""
        from script_utils import format_analysis_for_display

        from shesha.models import AnalysisComponent, RepoAnalysis

        comp = AnalysisComponent(
            name="API Server",
            path="api/",
            description="REST API for user management",
            apis=[{"type": "rest", "endpoints": ["/users", "/auth"]}],
            models=["User", "Session"],
            entry_points=["api/main.py"],
            internal_dependencies=[],
        )
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test",
            components=[comp],
            external_dependencies=[],
        )

        output = format_analysis_for_display(analysis)

        assert "API Server" in output
        assert "api/" in output
        assert "REST API for user management" in output
        assert "User" in output

    def test_format_analysis_includes_caveats(self):
        """Formatted analysis includes caveats warning."""
        from script_utils import format_analysis_for_display

        from shesha.models import RepoAnalysis

        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="Test",
            components=[],
            external_dependencies=[],
            caveats="This may be wrong.",
        )

        output = format_analysis_for_display(analysis)

        assert "This may be wrong." in output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_script_utils.py::TestFormatAnalysisForDisplay -v`
Expected: FAIL with "cannot import name 'format_analysis_for_display'"

**Step 3: Write minimal implementation**

Add to `examples/script_utils.py`:

```python
def format_analysis_for_display(analysis: "RepoAnalysis") -> str:
    """Format a RepoAnalysis for terminal display.

    Args:
        analysis: The analysis to format.

    Returns:
        Formatted string suitable for terminal output.
    """
    from shesha.models import RepoAnalysis  # Type hint import

    lines: list[str] = []

    # Header
    date = analysis.generated_at[:10]
    sha = analysis.head_sha[:8] if analysis.head_sha else "unknown"
    lines.append(f"=== Codebase Analysis (generated {date}) ===")
    lines.append(f"Git SHA: {sha}")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append(analysis.overview)
    lines.append("")

    # Components
    if analysis.components:
        lines.append("## Components")
        for comp in analysis.components:
            lines.append(f"\n### {comp.name} ({comp.path})")
            lines.append(comp.description)
            if comp.apis:
                api_strs = []
                for api in comp.apis:
                    api_type = api.get("type", "unknown")
                    endpoints = api.get("endpoints", api.get("operations", api.get("commands", [])))
                    if endpoints:
                        api_strs.append(f"{api_type}: {', '.join(endpoints[:3])}")
                if api_strs:
                    lines.append(f"  APIs: {'; '.join(api_strs)}")
            if comp.models:
                lines.append(f"  Models: {', '.join(comp.models)}")
            if comp.entry_points:
                lines.append(f"  Entry points: {', '.join(comp.entry_points)}")

    # External dependencies
    if analysis.external_dependencies:
        lines.append("\n## External Dependencies")
        for dep in analysis.external_dependencies:
            opt = " (optional)" if dep.optional else ""
            lines.append(f"  - {dep.name}{opt}: {dep.description}")

    # Caveat
    lines.append(f"\n  {analysis.caveats}")

    return "\n".join(lines)
```

Also add the TYPE_CHECKING import at the top of script_utils.py:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shesha.models import RepoAnalysis
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_script_utils.py::TestFormatAnalysisForDisplay -v`
Expected: PASS

**Step 5: Commit**

```bash
git add examples/script_utils.py tests/unit/test_script_utils.py
git commit -m "feat(script_utils): add format_analysis_for_display"
```

---

## Task 15: Integrate Analysis Commands into repo.py

**Files:**
- Modify: `examples/repo.py`

**Step 1: Update imports in repo.py**

Add to the imports from script_utils:

```python
from script_utils import (
    ThinkingSpinner,
    format_analysis_for_display,
    format_history_prefix,
    format_progress,
    format_stats,
    format_thought_time,
    install_urllib3_cleanup_hook,
    is_analysis_command,
    is_exit_command,
    is_help_command,
    is_regenerate_command,
    is_write_command,
    parse_write_command,
    should_warn_history_size,
    write_session,
)
```

**Step 2: Update INTERACTIVE_HELP**

```python
INTERACTIVE_HELP = """\
Shesha Repository Explorer - Ask questions about the indexed codebase.

Commands:
  help, ?              Show this help message
  analysis             Show codebase analysis
  analyze              Generate/regenerate codebase analysis
  write                Save session transcript (auto-generated filename)
  write <filename>     Save session transcript to specified file
  quit, exit           Leave the session"""
```

**Step 3: Add analysis status check after project load**

Find the section where the project is loaded (around line 478-500) and add analysis status checking. Add this helper function before `run_interactive_loop`:

```python
def check_and_prompt_analysis(shesha: Shesha, project_id: str) -> None:
    """Check analysis status and prompt user if needed.

    Args:
        shesha: Shesha instance.
        project_id: Project to check.
    """
    try:
        status = shesha.get_analysis_status(project_id)
    except ValueError:
        return  # Project doesn't exist or other error

    if status == "missing":
        print("Note: No codebase analysis exists for this repository.")
        try:
            response = input("Generate analysis? (y/n): ").strip().lower()
            if response == "y":
                print("Generating analysis (this may take a minute)...")
                shesha.generate_analysis(project_id)
                print("Analysis complete.")
        except (EOFError, KeyboardInterrupt):
            print()  # Clean line after interrupt
    elif status == "stale":
        print("Note: Codebase analysis is outdated (HEAD has moved).")
        try:
            response = input("Regenerate analysis? (y/n): ").strip().lower()
            if response == "y":
                print("Regenerating analysis...")
                shesha.generate_analysis(project_id)
                print("Analysis updated.")
        except (EOFError, KeyboardInterrupt):
            print()
```

**Step 4: Add analysis commands to interactive loop**

In `run_interactive_loop`, add handling after the help command check:

```python
        if is_analysis_command(user_input):
            analysis = project._storage.load_analysis(project.project_id)
            if analysis is None:
                print("No analysis exists. Use 'analyze' to generate one.")
            else:
                print(format_analysis_for_display(analysis))
            print()
            continue

        if is_regenerate_command(user_input):
            print("Generating analysis (this may take a minute)...")
            try:
                # Access shesha through a closure or pass it as parameter
                # For now, we'll need to modify run_interactive_loop signature
                analysis = project.query("Analyze this codebase")  # Simplified
                print("Analysis complete. Use 'analysis' to view.")
            except Exception as e:
                print(f"Error generating analysis: {e}")
            print()
            continue
```

**Step 5: Update run_interactive_loop signature to accept shesha**

```python
def run_interactive_loop(
    project: Project, verbose: bool, project_name: str, shesha: Shesha
) -> None:
```

And update the regenerate command handler to use shesha:

```python
        if is_regenerate_command(user_input):
            print("Generating analysis (this may take a minute)...")
            try:
                shesha.generate_analysis(project.project_id)
                print("Analysis complete. Use 'analysis' to view.")
            except Exception as e:
                print(f"Error generating analysis: {e}")
            print()
            continue
```

**Step 6: Update main() to pass shesha and call analysis check**

In main(), after loading the project, add:

```python
    # Check analysis status
    check_and_prompt_analysis(shesha, project.project_id)

    # Enter interactive loop
    run_interactive_loop(project, args.verbose, project.project_id, shesha)
```

**Step 7: Commit**

```bash
git add examples/repo.py
git commit -m "feat(repo.py): add analysis status alerts and commands"
```

---

## Task 16: Create recon_with_analysis Prompt

**Files:**
- Create: `src/shesha/experimental/multi_repo/prompts/recon_with_analysis.md`

**Step 1: Create the prompt file**

Create `src/shesha/experimental/multi_repo/prompts/recon_with_analysis.md`:

```markdown
# Repository Reconnaissance (with existing analysis)

An existing codebase analysis has been provided below. Use it as a guide to understand the repository structure, but verify and supplement it by exploring the actual code.

## Existing Analysis

{existing_analysis}

## Your Task

Using the existing analysis as context:

1. **Verify** the analysis is accurate by checking the actual code
2. **Supplement** with any APIs, models, or entry points the analysis missed
3. **Update** any information that appears outdated or incorrect

Focus on extracting:
- Public APIs (REST endpoints, GraphQL operations, gRPC services, CLI commands)
- Data models and schemas
- Entry points and handlers
- External dependencies

## Output Format

Return a JSON object:

```json
{
  "apis": ["GET /api/users", "POST /api/auth/login"],
  "models": ["User", "Session", "AuthToken"],
  "entry_points": ["src/main.py", "src/api/routes.py"],
  "dependencies": ["PostgreSQL", "Redis", "auth-service"]
}
```

Note: The `dependencies` field should list both external services AND internal dependencies on other repositories/services that this codebase interacts with.
```

**Step 2: Commit**

```bash
git add src/shesha/experimental/multi_repo/prompts/recon_with_analysis.md
git commit -m "feat(multi-repo): add recon_with_analysis prompt"
```

---

## Task 17: Integrate Analysis into Multi-Repo Analyzer

**Files:**
- Modify: `src/shesha/experimental/multi_repo/analyzer.py`
- Test: `tests/experimental/multi_repo/test_analyzer.py`

**Step 1: Write the failing test**

Add to `tests/experimental/multi_repo/test_analyzer.py`:

```python
class TestAnalyzerWithAnalysis:
    """Tests for analyzer using existing analysis."""

    def test_run_recon_uses_analysis_when_available(self, analyzer, mock_project):
        """_run_recon injects analysis context when available."""
        from shesha.models import AnalysisComponent, RepoAnalysis

        # Create analysis
        analysis = RepoAnalysis(
            version="1",
            generated_at="2026-02-06T10:30:00Z",
            head_sha="abc123",
            overview="A test service.",
            components=[
                AnalysisComponent(
                    name="API",
                    path="api/",
                    description="REST API",
                    apis=[{"type": "rest", "endpoints": ["/users"]}],
                    models=["User"],
                    entry_points=["main.py"],
                    internal_dependencies=[],
                )
            ],
            external_dependencies=[],
        )
        analyzer._shesha.get_analysis.return_value = analysis

        # Run recon
        analyzer._run_recon("test-project")

        # Verify query was called with analysis context
        call_args = mock_project.query.call_args
        prompt = call_args[0][0]
        assert "A test service." in prompt or "existing analysis" in prompt.lower()

    def test_run_recon_without_analysis_uses_standard_prompt(self, analyzer, mock_project):
        """_run_recon uses standard prompt when no analysis exists."""
        analyzer._shesha.get_analysis.return_value = None

        analyzer._run_recon("test-project")

        # Verify standard recon prompt was used (no analysis context)
        call_args = mock_project.query.call_args
        prompt = call_args[0][0]
        assert "existing analysis" not in prompt.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/experimental/multi_repo/test_analyzer.py::TestAnalyzerWithAnalysis -v`
Expected: FAIL (test setup may need adjustment based on existing fixtures)

**Step 3: Write minimal implementation**

Update `src/shesha/experimental/multi_repo/analyzer.py`:

Add the `_format_analysis_context` method:

```python
    def _format_analysis_context(self, analysis: "RepoAnalysis") -> str:
        """Format analysis for injection into recon prompt.

        Args:
            analysis: The analysis to format.

        Returns:
            Formatted string for prompt injection.
        """
        from shesha.models import RepoAnalysis  # Avoid circular import

        lines = [f"Overview: {analysis.overview}", "", "Components:"]

        for comp in analysis.components:
            lines.append(f"- {comp.name} ({comp.path}): {comp.description}")
            if comp.apis:
                for api in comp.apis:
                    api_type = api.get("type", "unknown")
                    endpoints = api.get("endpoints", [])
                    if endpoints:
                        lines.append(f"  APIs ({api_type}): {', '.join(endpoints[:5])}")
            if comp.models:
                lines.append(f"  Models: {', '.join(comp.models)}")

        if analysis.external_dependencies:
            lines.append("")
            lines.append("External Dependencies:")
            for dep in analysis.external_dependencies:
                lines.append(f"- {dep.name} ({dep.type}): {dep.description}")

        return "\n".join(lines)
```

Update the `_run_recon` method:

```python
    def _run_recon(self, project_id: str) -> RepoSummary:
        """Run Phase 1 recon on a single project.

        Args:
            project_id: The project to analyze.

        Returns:
            RepoSummary with extracted structure.
        """
        project = self._shesha.get_project(project_id)

        # Check for existing analysis
        analysis = self._shesha.get_analysis(project_id)

        if analysis:
            # Use analysis-enhanced prompt
            context = self._format_analysis_context(analysis)
            prompt_template = self._load_prompt("recon_with_analysis")
            prompt = prompt_template.replace("{existing_analysis}", context)
        else:
            # Use standard recon prompt
            prompt = self._load_prompt("recon")

        result = project.query(prompt)
        answer = result.answer

        # Try to extract structured data
        data = self._extract_json(answer)

        if data:
            return RepoSummary(
                project_id=project_id,
                apis=data.get("apis", []),
                models=data.get("models", []),
                entry_points=data.get("entry_points", []),
                dependencies=data.get("dependencies", []),
                raw_summary=answer,
            )

        # Fallback: return raw answer with empty lists
        return RepoSummary(
            project_id=project_id,
            raw_summary=answer,
        )
```

Add the import at top (in TYPE_CHECKING block):

```python
if TYPE_CHECKING:
    from shesha import Shesha
    from shesha.models import RepoAnalysis
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/experimental/multi_repo/test_analyzer.py::TestAnalyzerWithAnalysis -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/shesha/experimental/multi_repo/analyzer.py tests/experimental/multi_repo/test_analyzer.py
git commit -m "feat(multi-repo): integrate analysis into recon phase"
```

---

## Task 18: Run Full Test Suite and Fix Any Issues

**Step 1: Run full test suite**

Run: `pytest -v`

**Step 2: Fix any failing tests**

Address any test failures that arise from the integration.

**Step 3: Run linting and type checking**

Run: `make all`

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: fix any remaining issues from analysis feature"
```

---

## Summary

This implementation plan covers:

1. **Tasks 1-3**: Data models (AnalysisComponent, AnalysisExternalDep, RepoAnalysis)
2. **Tasks 4-5**: Storage backend updates (protocol + filesystem implementation)
3. **Tasks 6-7**: Shesha API methods (get_analysis_status, get_analysis)
4. **Tasks 8-10**: Analysis generator module with prompt and generate()
5. **Tasks 11-12**: Shesha generate_analysis method and ProjectInfo update
6. **Tasks 13-15**: repo.py CLI integration (commands and status alerts)
7. **Tasks 16-17**: Multi-repo analyzer integration
8. **Task 18**: Final verification

Each task follows TDD: write failing test → implement → verify → commit.
