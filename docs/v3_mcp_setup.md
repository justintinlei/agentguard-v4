# V3 MCP Setup — Why Two Toolchains (Planned)

This documents **why** v3 needs both a Python toolchain and a Node.js
toolchain, before either gets installed. Nothing in this file has been run
yet — `node`, `npx`, and the Python `mcp` package are all still absent
from this machine and this `.venv`, confirmed before writing this doc.
Actually installing them is later labs' job, not this one:

- Day 2 Lab 3 installs Node.js (via Homebrew).
- Day 2 Lab 4 installs the Python `mcp` package into this project's
  `.venv`.
- Day 2 Lab 5 verifies the `fastmcp` import actually works.
- Day 2 Lab 6 launches the MCP Inspector with `npx`.

## Why one project needs two languages

MCP is a **protocol** — a defined message format — not tied to any one
programming language. That's the whole reason two toolchains are
required here, not a workaround:

- **The MCP server will be Python**, because the rest of AgentGuard
  (`scanner.py`, the v2 grounded analyst, the Streamlit app) is already
  Python. There's no reason to introduce a second server language just
  for the discovery layer.
- **The MCP Inspector is Node.js**, because it's an official,
  general-purpose developer tool maintained separately from any one
  server implementation. It doesn't care what language the server is
  written in — it only ever talks to the server *through the protocol*,
  the same way a web browser doesn't care what language a website's
  backend runs.

A Python server and a Node-based Inspector can talk to each other because
they both speak MCP — not because they share a runtime.

## New terms

- **Runtime** — the environment needed to actually execute a program in a
  given language. Python code needs the Python interpreter (this
  project's `.venv`); JavaScript/Node.js code needs the separate Node.js
  runtime. Installing one does not install the other.
- **npm** — Node's package manager, the JavaScript equivalent of Python's
  `pip`.
- **npx** — a tool bundled with npm that downloads and runs a package's
  command-line tool on the spot, without a permanent global install. This
  is why the Inspector is launched as `npx
  @modelcontextprotocol/inspector` rather than something installed once
  and kept around.
- **MCP Inspector** — an official, language-agnostic developer tool for
  interactively testing any MCP server (call a tool, inspect the raw
  response), regardless of what language the server itself is
  implemented in.
- **Language-agnostic protocol** — a message format any language can
  implement, so implementations written in different languages can still
  interoperate correctly.

## What later labs will actually install (not done yet)

- Python: `pip install "mcp[cli]>=2,<3"` inside this project's `.venv`,
  then verify `from mcp.server import MCPServer` and `from mcp import
  Client` both import cleanly.
- Node.js: installed via Homebrew, then the Inspector run on demand with
  `npx @modelcontextprotocol/inspector` — never installed permanently,
  since `npx` fetches and runs it fresh each time.

## Security note

Two separate toolchains also means two separate places dependencies get
pulled from (PyPI for Python, npm for Node) — worth knowing when Day 9's
secret-scan and dependency-review labs come around, since each ecosystem
has its own supply-chain considerations. Nothing about that changes v1's
scanning authority or v2's grounding guarantee; it's purely about how the
discovery layer's own tooling is assembled.
