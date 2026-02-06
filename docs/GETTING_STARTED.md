# Getting Started with Shesha

Now that you have completed the installation, follow these steps to perform your first research with Shesha.

## 1. Set Your API Key

Shesha needs an LLM to think. Set your preferred provider's key (Anthropic is recommended for complex reasoning):

```bash
export ANTHROPIC_API_KEY="your-key-here"
# OR
export OPENAI_API_KEY="your-key-here"
```

## 2. Ingest a Repository

To ask questions about a codebase, you first need to "ingest" it. This parses the files and stores them in a local project. Let's ingest the Shesha codebase itself:

```bash
# From the repo root
python -m shesha.librarian ingest --path . --name shesha-audit
```

## 3. Ask Your First Question

Now you can ask complex questions. Shesha will spin up a secure Docker sandbox, write Python code to explore the files, and give you an answer with citations.

```bash
python -m shesha.librarian query --project shesha-audit "How does the system audit ensure the Python version is correct?"
```

### What to expect:
1. **Thought Loop**: You'll see Shesha "thinking" as it decides which files to read.
2. **Execution**: It will run code to analyze the logic in `src/shesha/librarian/cli.py`.
3. **Citations**: The final answer will include `file:line` references to the exact code it found.

## 4. Connect to Claude Desktop (Optional)

If you prefer using an AI interface like Claude, you can use the MCP server:

1. Locate the `mcp-server-readme.md` file in your root directory.
2. Copy the JSON configuration provided there.
3. Paste it into your `claude_desktop_config.json`.
4. Restart Claude and look for the 🔌 icon!

## Frequently Asked Questions

### Do I need to run `librarian install` after every reboot?
**No.** The installation is a one-time setup. It creates your persistent storage and configuration. 

On a fresh reboot, you only need to:
1. Ensure **Docker Desktop** (or your Docker engine) is running.
2. Activate your virtual environment: `source .venv/bin/activate`.
3. Set your API Key (e.g., `export ANTHROPIC_API_KEY=...`).
4. Run your commands (`query`, `ingest`, etc.).

### How do I gracefully shut down?
*   **CLI Commands**: `query` and `ingest` are tasks that finish and exit automatically.
*   **MCP Server**: When running as an MCP server, Shesha is managed by your AI client (like Claude Desktop). It starts and stops automatically when the client does.
*   **Manual Stop**: If you are running a command and want to stop it immediately, use `Ctrl+C`. Shesha has built-in cleanup logic to ensure any active Docker sandboxes are stopped and reaped.
*   **Docker Cleanup**: If you ever want to manually clear the sandbox image, you can run `docker rmi shesha-sandbox`.

## Next Steps
- Explore more commands with `python -m shesha.librarian --help`.
- Learn about advanced configuration in [docs/ENVIRONMENT.md](./ENVIRONMENT.md).
- Check the [Architectural Overview](./ARCHITECTURE.md) to understand how the RLM loop works.
