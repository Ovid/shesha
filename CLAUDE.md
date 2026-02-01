# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shesha is a Python library implementing Recursive Language Models (RLMs) based on arXiv:2512.24601v1. It enables querying document collections by having an LLM write Python code to explore documents in a REPL, with recursive sub-LLM calls for divide-and-conquer strategies.

**Core concept:** Documents are loaded as variables in a sandboxed Python REPL. The LLM generates code to explore them, sees output, and repeats until calling `FINAL("answer")`.

## Architecture

```
User Query → RLM Core Loop → Docker Sandbox (code execution)
                ↓                    ↓
           LiteLLM Client      llm_query() for sub-calls
                ↓
         Trace Recorder (full observability)
```

**Key components:**
- `shesha/rlm/` - Core REPL+LLM loop, terminates on FINAL() or FINAL_VAR()
- `shesha/sandbox/` - Docker container pool with warm containers, network-isolated
- `shesha/storage/` - Pluggable backend (filesystem default)
- `shesha/parser/` - Document extraction (PDF, Word, HTML, code, text)
- `shesha/llm/` - LiteLLM wrapper for 100+ providers

**Security model:** Sub-LLM calls use `llm_query(instruction, content)` where instruction is trusted (from root LLM) and content is untrusted (wrapped in `<untrusted_document_content>` tags). Containers have egress whitelist (LLM APIs only).

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run single test
pytest tests/path/to/test.py::test_name -v

# Type checking
mypy src/shesha

# Linting
ruff check src tests
ruff format src tests

# Build sandbox container
docker build -t shesha-sandbox -f src/shesha/sandbox/Dockerfile .
```

## Development Workflow

This project uses TDD. For each feature:
1. Write failing test first
2. Implement minimal code to pass
3. Commit frequently with descriptive messages

## Key Design Decisions

- **Sub-LLM depth = 1:** Sub-calls are plain LLM (not recursive RLM) for predictable cost
- **Max iterations = 20:** Configurable limit on REPL loop cycles
- **Container pool:** Pre-warmed containers (default 3) to reduce latency
- **Projects:** Documents organized into projects for clean separation
