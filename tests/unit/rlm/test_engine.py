"""Tests for RLM engine."""

from unittest.mock import MagicMock, patch

from shesha.rlm.engine import QueryResult, RLMEngine, extract_code_blocks


def test_extract_code_blocks_finds_repl():
    """extract_code_blocks finds ```repl blocks."""
    text = """Here is some code:

```repl
print("hello")
```

And more text."""
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert 'print("hello")' in blocks[0]


def test_extract_code_blocks_finds_python():
    """extract_code_blocks also finds ```python blocks."""
    text = """```python
x = 1
```"""
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert "x = 1" in blocks[0]


def test_query_result_dataclass():
    """QueryResult stores query results."""
    from shesha.rlm.trace import TokenUsage, Trace

    result = QueryResult(
        answer="The answer",
        trace=Trace(),
        token_usage=TokenUsage(100, 50),
        execution_time=1.5,
    )
    assert result.answer == "The answer"
    assert result.execution_time == 1.5


class TestRLMEngine:
    """Tests for RLMEngine."""

    @patch("shesha.rlm.engine.ContainerExecutor")
    @patch("shesha.rlm.engine.LLMClient")
    def test_engine_runs_until_final(
        self,
        mock_llm_cls: MagicMock,
        mock_executor_cls: MagicMock,
    ):
        """Engine runs until FINAL is called."""
        # Mock LLM to return code with FINAL
        mock_llm = MagicMock()
        mock_llm.complete.return_value = MagicMock(
            content='```repl\nFINAL("The answer is 42")\n```',
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        mock_llm_cls.return_value = mock_llm

        # Mock executor
        mock_executor = MagicMock()
        mock_executor.execute.return_value = MagicMock(
            status="ok",
            stdout="",
            stderr="",
            error=None,
            final_answer="The answer is 42",
        )
        mock_executor_cls.return_value = mock_executor

        engine = RLMEngine(model="test-model")
        result = engine.query(
            documents=["Doc 1 content", "Doc 2 content"],
            question="What is the answer?",
        )

        assert result.answer == "The answer is 42"
        assert len(result.trace.steps) > 0
