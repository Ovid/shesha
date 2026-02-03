#!/usr/bin/env python3
"""Shared utilities for Shesha example scripts."""

import threading
import time

from shesha.rlm.trace import StepType, TokenUsage, Trace


class ThinkingSpinner:
    """Animated spinner that shows 'Thinking...' with animated dots."""

    def __init__(self) -> None:
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the spinner animation."""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        # Clear the line
        print("\r" + " " * 20 + "\r", end="", flush=True)

    def _animate(self) -> None:
        """Animation loop running in background thread."""
        dots = 0
        while self._running:
            dots = (dots % 3) + 1
            print(f"\rThinking{'.' * dots}{' ' * (3 - dots)}", end="", flush=True)
            time.sleep(0.3)


def format_progress(
    step_type: StepType, iteration: int, content: str, elapsed_seconds: float | None = None
) -> str:
    """Format a progress message for verbose output."""
    step_names = {
        StepType.CODE_GENERATED: "Generating code",
        StepType.CODE_OUTPUT: "Executing code",
        StepType.SUBCALL_REQUEST: "Sub-LLM query",
        StepType.SUBCALL_RESPONSE: "Sub-LLM response",
        StepType.FINAL_ANSWER: "Final answer",
        StepType.ERROR: "Error",
    }
    step_name = step_names.get(step_type, step_type.value)
    if elapsed_seconds is not None:
        return f"  [{elapsed_seconds:.1f}s] [Iteration {iteration + 1}] {step_name}"
    return f"  [Iteration {iteration + 1}] {step_name}"


def format_thought_time(elapsed_seconds: float) -> str:
    """Format elapsed time as '[Thought for N seconds]'."""
    seconds = round(elapsed_seconds)
    unit = "second" if seconds == 1 else "seconds"
    return f"[Thought for {seconds} {unit}]"


def format_stats(execution_time: float, token_usage: TokenUsage, trace: Trace) -> str:
    """Format verbose stats for display after an answer."""
    prompt = token_usage.prompt_tokens
    completion = token_usage.completion_tokens
    total = token_usage.total_tokens
    lines = [
        "---",
        f"Execution time: {execution_time:.2f}s",
        f"Tokens: {total} (prompt: {prompt}, completion: {completion})",
        f"Trace steps: {len(trace.steps)}",
    ]
    return "\n".join(lines)
