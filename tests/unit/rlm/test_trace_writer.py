"""Tests for trace writer."""

import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from shesha.models import QueryContext
from shesha.rlm.trace import StepType, TokenUsage, Trace
from shesha.storage.filesystem import FilesystemStorage


class TestTraceWriterFileCreation:
    """Tests for trace file creation."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FilesystemStorage:
        """Create a temporary storage backend."""
        storage = FilesystemStorage(root_path=tmp_path)
        storage.create_project("test-project")
        return storage

    @pytest.fixture
    def trace(self) -> Trace:
        """Create a sample trace."""
        trace = Trace()
        trace.add_step(StepType.CODE_GENERATED, "print('hello')", iteration=0)
        trace.add_step(StepType.CODE_OUTPUT, "hello", iteration=0)
        return trace

    @pytest.fixture
    def context(self) -> QueryContext:
        """Create a sample query context."""
        return QueryContext(
            trace_id="abcd1234-5678-90ab-cdef-1234567890ab",
            question="What is the answer?",
            document_ids=["doc1", "doc2"],
            model="claude-sonnet-4-20250514",
            system_prompt="You are an assistant...",
            subcall_prompt="Analyze this...",
        )

    def test_write_trace_creates_jsonl_file(
        self,
        storage: FilesystemStorage,
        trace: Trace,
        context: QueryContext,
    ) -> None:
        """write_trace creates a .jsonl file in the traces directory."""
        from shesha.rlm.trace_writer import TraceWriter

        writer = TraceWriter(storage)
        # Mock datetime to get predictable filename
        fixed_time = datetime.datetime(2026, 2, 3, 14, 30, 0, 123000, tzinfo=datetime.UTC)
        with patch("shesha.rlm.trace_writer.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fixed_time
            mock_dt.datetime.fromtimestamp = datetime.datetime.fromtimestamp
            mock_dt.UTC = datetime.UTC
            path = writer.write_trace(
                project_id="test-project",
                trace=trace,
                context=context,
                answer="42",
                token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
                execution_time=1.5,
                status="success",
            )

        assert path.exists()
        assert path.suffix == ".jsonl"
        assert path.parent.name == "traces"
        # Check filename format: YYYY-MM-DDTHH-MM-SS-mmm_shortid.jsonl
        assert "2026-02-03T14-30-00-123" in path.name
        assert "abcd1234" in path.name


class TestTraceWriterContent:
    """Tests for trace file content."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FilesystemStorage:
        """Create a temporary storage backend."""
        storage = FilesystemStorage(root_path=tmp_path)
        storage.create_project("test-project")
        return storage

    @pytest.fixture
    def trace(self) -> Trace:
        """Create a sample trace."""
        trace = Trace()
        trace.add_step(StepType.CODE_GENERATED, "print('hello')", iteration=0)
        trace.add_step(StepType.CODE_OUTPUT, "hello", iteration=0)
        return trace

    @pytest.fixture
    def context(self) -> QueryContext:
        """Create a sample query context."""
        return QueryContext(
            trace_id="abcd1234-5678-90ab-cdef-1234567890ab",
            question="What is the answer?",
            document_ids=["doc1", "doc2"],
            model="claude-sonnet-4-20250514",
            system_prompt="You are an assistant...",
            subcall_prompt="Analyze this...",
        )

    def test_trace_file_contains_header_with_metadata(
        self,
        storage: FilesystemStorage,
        trace: Trace,
        context: QueryContext,
    ) -> None:
        """First line of trace file is header with query metadata."""
        from shesha.rlm.trace_writer import TraceWriter

        writer = TraceWriter(storage)
        path = writer.write_trace(
            project_id="test-project",
            trace=trace,
            context=context,
            answer="42",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            execution_time=1.5,
            status="success",
        )

        lines = path.read_text().strip().split("\n")
        header = json.loads(lines[0])

        assert header["type"] == "header"
        assert header["trace_id"] == "abcd1234-5678-90ab-cdef-1234567890ab"
        assert header["question"] == "What is the answer?"
        assert header["document_ids"] == ["doc1", "doc2"]
        assert header["model"] == "claude-sonnet-4-20250514"
        assert header["system_prompt"] == "You are an assistant..."
        assert header["subcall_prompt"] == "Analyze this..."
        assert "timestamp" in header

    def test_trace_file_contains_all_steps(
        self,
        storage: FilesystemStorage,
        context: QueryContext,
    ) -> None:
        """Trace file contains one line per step with correct fields."""
        from shesha.rlm.trace_writer import TraceWriter

        trace = Trace()
        trace.add_step(StepType.CODE_GENERATED, "print('hello')", iteration=0, tokens_used=50)
        trace.add_step(StepType.CODE_OUTPUT, "hello", iteration=0, duration_ms=100)
        trace.add_step(StepType.FINAL_ANSWER, "42", iteration=0)

        writer = TraceWriter(storage)
        path = writer.write_trace(
            project_id="test-project",
            trace=trace,
            context=context,
            answer="42",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            execution_time=1.5,
            status="success",
        )

        lines = path.read_text().strip().split("\n")
        # Header + 3 steps + summary = 5 lines
        assert len(lines) >= 4  # At least header + 3 steps

        # Check step lines (lines 1, 2, 3)
        step1 = json.loads(lines[1])
        assert step1["type"] == "step"
        assert step1["step_type"] == "code_generated"
        assert step1["iteration"] == 0
        assert step1["content"] == "print('hello')"
        assert step1["tokens_used"] == 50

        step2 = json.loads(lines[2])
        assert step2["type"] == "step"
        assert step2["step_type"] == "code_output"
        assert step2["duration_ms"] == 100

        step3 = json.loads(lines[3])
        assert step3["type"] == "step"
        assert step3["step_type"] == "final_answer"

    def test_trace_file_ends_with_summary(
        self,
        storage: FilesystemStorage,
        trace: Trace,
        context: QueryContext,
    ) -> None:
        """Last line of trace file is summary with totals."""
        from shesha.rlm.trace_writer import TraceWriter

        writer = TraceWriter(storage)
        path = writer.write_trace(
            project_id="test-project",
            trace=trace,
            context=context,
            answer="42",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50),
            execution_time=1.5,
            status="success",
        )

        lines = path.read_text().strip().split("\n")
        summary = json.loads(lines[-1])

        assert summary["type"] == "summary"
        assert summary["answer"] == "42"
        assert summary["total_iterations"] == 1  # iteration 0 = 1 iteration
        assert summary["total_tokens"] == {"prompt": 100, "completion": 50}
        assert summary["total_duration_ms"] == 1500
        assert summary["status"] == "success"


class TestTraceWriterCleanup:
    """Tests for trace cleanup."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> FilesystemStorage:
        """Create a temporary storage backend."""
        storage = FilesystemStorage(root_path=tmp_path)
        storage.create_project("test-project")
        return storage

    def test_cleanup_removes_oldest_traces(self, storage: FilesystemStorage) -> None:
        """cleanup_old_traces removes oldest when over limit."""
        from shesha.rlm.trace_writer import TraceWriter

        traces_dir = storage.get_traces_dir("test-project")
        # Create 5 trace files
        for i in range(5):
            (traces_dir / f"2026-02-03T10-00-0{i}-000_aaaa{i}111.jsonl").write_text("{}")

        writer = TraceWriter(storage)
        writer.cleanup_old_traces("test-project", max_count=3)

        remaining = storage.list_traces("test-project")
        assert len(remaining) == 3
        # Oldest 2 should be deleted, newest 3 remain
        names = [p.name for p in remaining]
        assert "2026-02-03T10-00-02-000_aaaa2111.jsonl" in names
        assert "2026-02-03T10-00-03-000_aaaa3111.jsonl" in names
        assert "2026-02-03T10-00-04-000_aaaa4111.jsonl" in names

    def test_cleanup_does_nothing_under_limit(self, storage: FilesystemStorage) -> None:
        """cleanup_old_traces does nothing when under limit."""
        from shesha.rlm.trace_writer import TraceWriter

        traces_dir = storage.get_traces_dir("test-project")
        # Create 2 trace files
        (traces_dir / "2026-02-03T10-00-00-000_aaaa1111.jsonl").write_text("{}")
        (traces_dir / "2026-02-03T10-00-01-000_bbbb2222.jsonl").write_text("{}")

        writer = TraceWriter(storage)
        writer.cleanup_old_traces("test-project", max_count=5)

        remaining = storage.list_traces("test-project")
        assert len(remaining) == 2
