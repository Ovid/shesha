# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Shesha.check_repo_for_updates()` method to check if a cloned repository has updates available
- `RepoIngester.get_repo_url()` method to retrieve the remote origin URL from a cloned repo

### Fixed

- `--update` flag in `examples/repo.py` now works when selecting an existing project from the picker

## [0.1.0] - 2025-01-01

### Added

- Initial release of Shesha RLM library
- Core RLM loop with configurable max iterations
- Docker sandbox for secure code execution
- Document loading for PDF, DOCX, HTML, and text files
- Sub-LLM queries via `llm_query()` function
- Project-based document organization
- LiteLLM integration for multiple LLM providers
- Trace recording for debugging and analysis
- Security hardening with untrusted content tagging
- Network isolation with egress whitelist for LLM APIs
