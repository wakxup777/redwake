# shell — `exec_command` + `write_stdin`

SDK-provided shell tools wired per-run from the sandbox session. Every CLI
invocation the agent makes (nmap, ffuf, agent-browser, python3, …) goes
through `exec_command`. `write_stdin` streams input to a still-running
process started by an earlier `exec_command` (for interactive prompts).

- **Implementation:** `agents.sandbox.capabilities.tools.shell_tool.ShellTool`
  (in the upstream `agents` SDK)
- **Wired in:** `redwake/agents/factory.py` — added per-run via the SDK
  `Shell` capability; `write_stdin` is wrapped to drop the SDK's `pid`
  arg from the function schema.
- **Sandbox env:** `http_proxy` / `https_proxy` route every shell child
  through Caido; `AGENT_BROWSER_*`, `REQUESTS_CA_BUNDLE` etc. come from
  `containers/Dockerfile`.
