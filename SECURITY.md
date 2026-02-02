# Security Policy

Note that your author is I<not> a security expert. I have tried to implement some basic sanity in this project, but you should probably review this carefully.

## Threat Model

Shesha executes LLM-generated code in Docker containers. The primary threats are:

1. **Prompt Injection**: Malicious content in documents attempting to manipulate the LLM
2. **Sandbox Escape**: Code attempting to break out of the container
3. **Data Exfiltration**: Attempts to send document data to external servers
4. **Resource Exhaustion**: Code consuming excessive CPU/memory

## Defense Layers

### 1. Prompt Injection Mitigation

- **Untrusted Content Tags**: All document content is wrapped in `<untrusted_document_content>` tags
- **Hardened System Prompt**: Explicit warnings about adversarial content
- **Instruction/Content Separation**: `llm_query(instruction, content)` keeps trusted instructions separate from untrusted document data

### 2. Docker Sandbox

- **Network Isolation**: Containers have no network access by default
- **Resource Limits**: Memory (512MB) and CPU (1 core) limits enforced
- **Execution Timeout**: 30-second timeout per code execution
- **Non-root User**: Code runs as unprivileged `sandbox` user
- **Read-only Filesystem**: No persistent writes allowed

### 3. Network Policy (When Enabled)

If network access is required for sub-LLM calls:
- **Egress Whitelist**: Only allowed to LLM API endpoints
- **No Inbound**: No incoming connections allowed

## Configuration

Security-relevant settings in `SheshaConfig`:

| Setting | Default | Description |
|---------|---------|-------------|
| `container_memory_mb` | 512 | Memory limit per container |
| `execution_timeout_sec` | 30 | Max execution time per code block |
| `max_output_chars` | 50000 | Truncate large outputs |
| `allowed_hosts` | LLM APIs only | Network egress whitelist |

## Reporting Vulnerabilities

Please report security vulnerabilities via GitHub Security Advisories.

## Disclaimer

Shesha provides defense-in-depth but cannot guarantee perfect isolation. Do not process highly sensitive documents without additional security review.
