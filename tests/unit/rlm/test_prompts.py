"""Tests for RLM prompts."""

from shesha.rlm.prompts import (
    MAX_SUBCALL_CHARS,
    build_subcall_prompt,
    build_system_prompt,
)


def test_system_prompt_contains_security_warning():
    """System prompt contains prompt injection warning."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=10000,
        doc_names=["a.txt", "b.txt", "c.txt"],
    )
    assert "untrusted" in prompt.lower()
    assert "adversarial" in prompt.lower() or "injection" in prompt.lower()


def test_system_prompt_contains_context_info():
    """System prompt contains context information."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=10000,
        doc_names=["a.txt", "b.txt", "c.txt"],
    )
    assert "3" in prompt  # doc count
    assert "a.txt" in prompt


def test_system_prompt_explains_final():
    """System prompt explains FINAL function."""
    prompt = build_system_prompt(
        doc_count=1,
        total_chars=100,
        doc_names=["doc.txt"],
    )
    assert "FINAL" in prompt


def test_subcall_prompt_wraps_content():
    """Subcall prompt wraps content in untrusted tags."""
    prompt = build_subcall_prompt(
        instruction="Summarize this",
        content="Document content here",
    )
    assert "<untrusted_document_content>" in prompt
    assert "</untrusted_document_content>" in prompt
    assert "Document content here" in prompt
    assert "Summarize this" in prompt


def test_system_prompt_contains_sub_llm_limit():
    """System prompt tells LLM about sub-LLM character limit."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=100000,
        doc_names=["a.txt", "b.txt", "c.txt"],
    )
    # Must mention the limit (500,000 formatted with commas)
    assert "500,000" in prompt or "500000" in prompt


def test_system_prompt_contains_chunking_guidance():
    """System prompt explains chunking strategy for large documents."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=100000,
        doc_names=["a.txt", "b.txt", "c.txt"],
    )
    prompt_lower = prompt.lower()
    # Must explain chunking strategy
    assert "chunk" in prompt_lower
    # Must mention buffer pattern for complex queries
    assert "buffer" in prompt_lower


def test_subcall_prompt_no_size_limit():
    """Subcall prompt passes content through without modification."""
    large_content = "x" * 600_000  # 600K chars

    prompt = build_subcall_prompt(
        instruction="Summarize this",
        content=large_content,
    )

    # Content should be passed through completely
    assert large_content in prompt
    assert "<untrusted_document_content>" in prompt


def test_system_prompt_requires_document_grounding():
    """System prompt instructs LLM to answer only from documents, not own knowledge."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=10000,
        doc_names=["a.txt", "b.txt", "c.txt"],
    )
    prompt_lower = prompt.lower()

    # Must instruct to use only documents
    assert "only" in prompt_lower and "document" in prompt_lower

    # Must instruct to not use own knowledge
    assert "own knowledge" in prompt_lower or "prior knowledge" in prompt_lower

    # Must instruct what to do if info not found
    assert "not found" in prompt_lower or "not contain" in prompt_lower


def test_system_prompt_includes_per_document_sizes():
    """System prompt shows size of each document when doc_sizes provided."""
    prompt = build_system_prompt(
        doc_count=3,
        total_chars=15000,
        doc_names=["a.txt", "b.txt", "c.txt"],
        doc_sizes=[5000, 4000, 6000],
    )
    # Should show each document with its size
    assert "context[0]" in prompt
    assert "a.txt" in prompt
    assert "5,000" in prompt
    assert "context[1]" in prompt
    assert "b.txt" in prompt
    assert "4,000" in prompt


def test_system_prompt_warns_about_oversized_documents():
    """System prompt warns when a document exceeds the sub-LLM limit."""
    oversized = MAX_SUBCALL_CHARS + 10000  # Slightly over limit
    prompt = build_system_prompt(
        doc_count=2,
        total_chars=oversized + 100000,
        doc_names=["small.txt", "large.txt"],
        doc_sizes=[100000, oversized],
    )
    # Should warn about the oversized document
    assert "EXCEEDS LIMIT" in prompt or "must chunk" in prompt.lower()
    # The small one should not have a warning
    assert "small.txt" in prompt


def test_system_prompt_explains_error_handling():
    """System prompt explains how to handle size limit errors."""
    prompt = build_system_prompt(
        doc_count=1,
        total_chars=1000,
        doc_names=["doc.txt"],
    )
    prompt_lower = prompt.lower()
    # Must explain what to do when hitting limit
    assert "error" in prompt_lower
    assert "retry" in prompt_lower or "chunk" in prompt_lower
