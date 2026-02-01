"""Tests for trace data classes."""

from shesha.rlm.trace import StepType, TokenUsage, Trace, TraceStep


def test_trace_step_creation():
    """TraceStep stores step information."""
    step = TraceStep(
        type=StepType.CODE_GENERATED,
        content="print('hello')",
        timestamp=1234567890.0,
        iteration=0,
        tokens_used=100,
        duration_ms=None,
    )
    assert step.type == StepType.CODE_GENERATED
    assert step.content == "print('hello')"
    assert step.iteration == 0


def test_trace_accumulates_steps():
    """Trace accumulates multiple steps."""
    trace = Trace()
    trace.add_step(
        type=StepType.CODE_GENERATED,
        content="code",
        iteration=0,
    )
    trace.add_step(
        type=StepType.CODE_OUTPUT,
        content="output",
        iteration=0,
    )
    assert len(trace.steps) == 2


def test_token_usage_total():
    """TokenUsage calculates total correctly."""
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
    assert usage.total_tokens == 150
