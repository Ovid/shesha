# Environment Variables

This document describes all environment variables used by Shesha.

## Getting Started

These are the only variables you need to run Shesha.

### SHESHA_API_KEY

**Required** for cloud LLM providers. Your API key for the LLM service.

```bash
export SHESHA_API_KEY="your-api-key-here"
```

The key format depends on your provider:
- **Anthropic**: `sk-ant-...`
- **OpenAI**: `sk-...`
- **Google**: Your Gemini API key

**Not required** when using Ollama (local models).

### SHESHA_MODEL

The LLM model to use. Defaults to `claude-sonnet-4-20250514`.

```bash
export SHESHA_MODEL="gpt-4o"  # or any supported model
```

#### Provider Examples

| Provider | Model Value | API Key Needed |
|----------|-------------|----------------|
| Anthropic | `claude-sonnet-4-20250514` | Yes |
| OpenAI | `gpt-4o`, `gpt-4-turbo` | Yes |
| Google | `gemini/gemini-1.5-pro` | Yes |
| Ollama | `ollama/llama3`, `ollama/mistral` | No |
| Azure | `azure/gpt-4` | Yes |
| AWS Bedrock | `bedrock/anthropic.claude-3` | AWS credentials |

#### Using Ollama (Free, Local)

Run models locally with no API key:

```bash
# Start Ollama and pull a model
ollama serve
ollama pull llama3

# Run Shesha with no API key needed
export SHESHA_MODEL="ollama/llama3"
python examples/barsoom.py
```

See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for the full list.

## Configuration Options

Optional settings for customizing Shesha's behavior.

### SHESHA_STORAGE_PATH

Directory where projects and documents are stored.

```bash
export SHESHA_STORAGE_PATH="./shesha_data"  # default
```

This directory contains:
- Uploaded documents organized by project
- Project metadata and settings
- Cached repository clones

### SHESHA_POOL_SIZE

Number of warm Docker containers kept ready for code execution.

```bash
export SHESHA_POOL_SIZE="3"  # default
```

Higher values improve response time for concurrent queries but use more memory. Each container uses approximately 50-100MB.

### SHESHA_MAX_ITERATIONS

Maximum RLM loop iterations before stopping.

```bash
export SHESHA_MAX_ITERATIONS="20"  # default
```

The RLM engine iterates: generate code → execute → observe output → repeat. This limit prevents runaway loops on difficult queries. Increase for complex multi-document analysis; decrease to limit token usage.

## Repository Authentication

Tokens for accessing private git repositories. Only needed when ingesting private repos.

### GITHUB_TOKEN

GitHub personal access token for private repositories.

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

Create a token at [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens). Required scope: `repo` (for private repositories).

### GITLAB_TOKEN

GitLab personal access token for private repositories.

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxx"
```

Create a token at GitLab → Preferences → Access Tokens. Required scope: `read_repository`.

### BITBUCKET_TOKEN

Bitbucket app password for private repositories.

```bash
export BITBUCKET_TOKEN="xxxxxxxxxxxx"
```

Create an app password at Bitbucket → Personal settings → App passwords. Required permission: `Repositories: Read`.

### Token Priority

When accessing repositories, Shesha checks in order:

1. Explicit `token` parameter passed to `create_project_from_repo()`
2. Environment variable for the host (`GITHUB_TOKEN`, etc.)
3. System git credentials (SSH keys, credential helpers)

Public repositories work without any token.

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SHESHA_API_KEY` | Yes* | — | LLM provider API key |
| `SHESHA_MODEL` | No | `claude-sonnet-4-20250514` | Model to use |
| `SHESHA_STORAGE_PATH` | No | `./shesha_data` | Project storage directory |
| `SHESHA_POOL_SIZE` | No | `3` | Warm container count |
| `SHESHA_MAX_ITERATIONS` | No | `20` | Max RLM loop iterations |
| `GITHUB_TOKEN` | No | — | GitHub private repo access |
| `GITLAB_TOKEN` | No | — | GitLab private repo access |
| `BITBUCKET_TOKEN` | No | — | Bitbucket private repo access |

*Not required when using Ollama.

## Programmatic Configuration

Environment variables can be overridden programmatically:

```python
from shesha import Shesha, SheshaConfig

config = SheshaConfig(
    model="gpt-4o",
    api_key="your-key",  # overrides SHESHA_API_KEY
    storage_path="./data",
    pool_size=5,
    max_iterations=30,
)
shesha = Shesha(config=config)
```

See [README.md](README.md#programmatic-configuration) for more configuration examples.
