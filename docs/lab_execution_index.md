# AgentGuard v3 Lab Execution Index

This is the reviewed, authoritative map between the manual, the starter-kit files, and the exact Claude Code prompt for every lab.

> Use the manual for teaching and click-by-click guidance. Use the matching prompt file for Claude Code. The file and command list below has been validated against this starter kit.

## Day 1 · Lab 1 · Understand The V3 Problem And Finish Line
- Estimated time: 50 minutes
- Learning purpose: why direct file access does not represent enterprise integrations and why a protocol boundary matters
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab01_understand-the-v3-problem-and-finish-line.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 2 · Copy The Released V2 Project Into A New V3 Folder
- Estimated time: 35 minutes
- Learning purpose: how to preserve the grounded analyst while creating a new integration release
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer` ; `cp -R agentguard-v2 agentguard-v3` ; `cd agentguard-v3` ; `pwd`
- Prompt: `prompts/course_labs/day01_lab02_copy-the-released-v2-project-into-a-new-v3-folder.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 3 · Open The V3 Project In All Working Tools
- Estimated time: 40 minutes
- Learning purpose: how Terminal, Cursor, Claude Code, GitHub Desktop, and Chrome divide responsibilities
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab03_open-the-v3-project-in-all-working-tools.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 4 · Create A V3 Branch And Baseline Commit
- Estimated time: 40 minutes
- Learning purpose: how a version boundary supports rollback and comparison
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab04_create-a-v3-branch-and-baseline-commit.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 5 · Run All V1 And V2 Regression Gates
- Estimated time: 50 minutes
- Learning purpose: how to prove the new integration work starts from a known-good product
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `scanner.py`, `tests/test_scanner.py`, `scripts/run_release_gate.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python scripts/run_release_gate.py`
- Prompt: `prompts/course_labs/day01_lab05_run-all-v1-and-v2-regression-gates.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 6 · Learn Mcp Host Client Server Tool Resource Transport And Sch
- Estimated time: 90 minutes
- Learning purpose: the protocol vocabulary needed to explain MCP clearly
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab06_learn-mcp-host-client-server-tool-resource-transport-and-sch.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 7 · Draw The V3 Trust Boundaries And Data Flow
- Estimated time: 60 minutes
- Learning purpose: where untrusted connected data enters and where validation occurs
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `docs/v3_architecture.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab07_draw-the-v3-trust-boundaries-and-data-flow.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 8 · Create The Day 1 Evidence And Learning Log
- Estimated time: 35 minutes
- Learning purpose: how to capture architectural learning before writing server code
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab08_create-the-day-1-evidence-and-learning-log.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 1 · Understand Why V3 Needs Both Python And Node Js Tools
- Estimated time: 50 minutes
- Learning purpose: why the server can be Python while the Inspector is launched with npx
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab01_understand-why-v3-needs-both-python-and-node-js-tools.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 2 · Check Existing Node Js And Npm Versions
- Estimated time: 30 minutes
- Learning purpose: how version commands confirm whether the Inspector prerequisites exist
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab02_check-existing-node-js-and-npm-versions.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 3 · Install Or Update Node Js With Homebrew
- Estimated time: 45 minutes
- Learning purpose: how Homebrew adds the Node runtime and npm package tool
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab03_install-or-update-node-js-with-homebrew.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 4 · Install The V3 Python Requirements In Venv
- Estimated time: 50 minutes
- Learning purpose: how the official MCP Python SDK becomes available only inside this project
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pip install --upgrade pip` ; `python -m pip install -r requirements.txt`
- Prompt: `prompts/course_labs/day02_lab04_install-the-v3-python-requirements-in-venv.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 5 · Verify The Mcp Package And Mcpserver Import
- Estimated time: 40 minutes
- Learning purpose: how a tiny import check catches environment mistakes early
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab05_verify-the-mcp-package-and-fastmcp-import.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 6 · Launch Mcp Inspector Help With Npx
- Estimated time: 40 minutes
- Learning purpose: how npx downloads and runs a temporary developer tool
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day02_lab06_launch-mcp-inspector-help-with-npx.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 7 · Review Stdio Transport And Logging Rules
- Estimated time: 60 minutes
- Learning purpose: why stdout carries protocol messages and logs must go to stderr
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python scripts/run_mcp_live_smoke.py`
- Prompt: `prompts/course_labs/day02_lab07_review-stdio-transport-and-logging-rules.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 8 · Run The V3 Setup Verifier And Save Evidence
- Estimated time: 35 minutes
- Learning purpose: how to confirm all runtimes before building the server
- Files: `notes/learning_log.md`, `requirements.txt`, `scripts/verify_setup.py`, `docs/v3_mcp_setup.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python scripts/verify_setup.py` ; `python scripts/check_no_secrets.py`
- Prompt: `prompts/course_labs/day02_lab08_run-the-v3-setup-verifier-and-save-evidence.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 1 · Define The Connected System Problem And Data Contract
- Estimated time: 55 minutes
- Learning purpose: what an enterprise registry must provide to AgentGuard
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab01_define-the-connected-system-problem-and-data-contract.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 2 · Create Connected Environment Agents Json
- Estimated time: 60 minutes
- Learning purpose: how the synthetic registry replaces v2 direct sample input
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m json.tool connected_environment/agents.json > /dev/null` ; `python -m json.tool connected_environment/tool_catalog.json > /dev/null` ; `python -m json.tool connected_environment/ownership.json > /dev/null`
- Prompt: `prompts/course_labs/day03_lab02_create-connected-environment-agents-json.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 3 · Create The Tool Catalog And Access Classifications
- Estimated time: 55 minutes
- Learning purpose: how tool metadata adds context beyond names
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab03_create-the-tool-catalog-and-access-classifications.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 4 · Create The Ownership Source
- Estimated time: 45 minutes
- Learning purpose: how separate systems can provide complementary agent context
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab04_create-the-ownership-source.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 5 · Create An Intentionally Malicious Untrusted Note
- Estimated time: 45 minutes
- Learning purpose: how connected content can contain prompt injection even when the transport is trusted
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab05_create-an-intentionally-malicious-untrusted-note.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 6 · Validate Every Json File Manually And With Python
- Estimated time: 55 minutes
- Learning purpose: how syntax validation prevents server failures
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m json.tool connected_environment/agents.json > /dev/null` ; `python -m json.tool connected_environment/tool_catalog.json > /dev/null` ; `python -m json.tool connected_environment/ownership.json > /dev/null`
- Prompt: `prompts/course_labs/day03_lab06_validate-every-json-file-manually-and-with-python.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 7 · Document Required Fields And Maximum Sizes
- Estimated time: 60 minutes
- Learning purpose: how schemas constrain the attack surface
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab07_document-required-fields-and-maximum-sizes.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 8 · Create Before State Evidence For The Connected Environment
- Estimated time: 40 minutes
- Learning purpose: how to show the inventory before AgentGuard discovery
- Files: `notes/learning_log.md`, `connected_environment/agents.json`, `connected_environment/tool_catalog.json`, `connected_environment/ownership.json`, `connected_environment/untrusted_notes.txt`, `docs/v3_data_contract.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day03_lab08_create-before-state-evidence-for-the-connected-environment.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 1 · Separate Pure Discovery Functions From Mcp Transport Code
- Estimated time: 55 minutes
- Learning purpose: why testable business logic should not depend on a running protocol server
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab01_separate-pure-discovery-functions-from-mcp-transport-code.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 2 · Create The Fixed Connected Environment File Allowlist
- Estimated time: 45 minutes
- Learning purpose: how the server refuses files the client was never authorized to select
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab02_create-the-fixed-connected-environment-file-allowlist.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 3 · Implement Safe Path Resolution
- Estimated time: 80 minutes
- Learning purpose: how resolve, parent checks, and fixed names block traversal
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab03_implement-safe-path-resolution.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 4 · Block Symbolic Link Escape And Unexpected File Types
- Estimated time: 70 minutes
- Learning purpose: how filesystem indirection can bypass naive path checks
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab04_block-symbolic-link-escape-and-unexpected-file-types.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 5 · Read Json With Sha 256 Provenance
- Estimated time: 60 minutes
- Learning purpose: how source hashes prove which connected inventory was scanned
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab05_read-json-with-sha-256-provenance.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 6 · Add Correlation Ids To Discovery Responses
- Estimated time: 45 minutes
- Learning purpose: how one request can be traced across server, adapter, scanner, and logs
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab06_add-correlation-ids-to-discovery-responses.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 7 · Implement List Get Catalog Ownership And Health Functions
- Estimated time: 85 minutes
- Learning purpose: how five narrow operations provide enough v3 value without write access
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab07_implement-list-get-catalog-ownership-and-health-functions.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 8 · Write Pure Core And Path Safety Tests
- Estimated time: 75 minutes
- Learning purpose: how negative tests prove forbidden access is rejected
- Files: `notes/learning_log.md`, `discovery_core.py`, `mcp_security.py`, `tests/test_discovery_core.py`, `tests/test_mcp_security.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_core.py tests/test_mcp_security.py`
- Prompt: `prompts/course_labs/day04_lab08_write-pure-core-and-path-safety-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 1 · Create The Mcpserver Server Skeleton
- Estimated time: 60 minutes
- Learning purpose: how the SDK turns Python functions into protocol tools
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab01_create-the-fastmcp-server-skeleton.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 2 · Expose The Health Check Tool
- Estimated time: 45 minutes
- Learning purpose: how a minimal tool validates transport before business data
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab02_expose-the-health-check-tool.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 3 · Expose List Agent Inventory
- Estimated time: 60 minutes
- Learning purpose: how AgentGuard receives the full synthetic inventory
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab03_expose-list-agent-inventory.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 4 · Expose Get Agent By Name With Input Validation
- Estimated time: 60 minutes
- Learning purpose: how narrow lookup inputs reduce ambiguity and abuse
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab04_expose-get-agent-by-name-with-input-validation.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 5 · Expose Tool Catalog And Ownership Tools
- Estimated time: 60 minutes
- Learning purpose: how separate sources remain separately auditable
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab05_expose-tool-catalog-and-ownership-tools.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 6 · Configure Logging To Stderr Only
- Estimated time: 45 minutes
- Learning purpose: how to avoid corrupting STDIO JSON-RPC messages
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab06_configure-logging-to-stderr-only.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 7 · Inspect The Server Tool List In Source Code
- Estimated time: 45 minutes
- Learning purpose: how to prove there are exactly five tools and no write operation
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab07_inspect-the-server-tool-list-in-source-code.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 8 · Run Server Level Static And Automated Checks
- Estimated time: 60 minutes
- Learning purpose: how imports, tests, and schemas establish a stable server before client work
- Files: `notes/learning_log.md`, `mcp_server.py`, `tests/test_mcp_sdk_contract.py`, `tests/test_discovery_core.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_sdk_contract.py tests/test_discovery_core.py`
- Prompt: `prompts/course_labs/day05_lab08_run-server-level-static-and-automated-checks.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 1 · Launch Mcp Inspector Against The Local Server
- Estimated time: 50 minutes
- Learning purpose: how an interactive protocol debugger exposes tools and responses
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day06_lab01_launch-mcp-inspector-against-the-local-server.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 2 · Call Health Check In Inspector
- Estimated time: 35 minutes
- Learning purpose: how to confirm transport initialization and read-only mode
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day06_lab02_call-health-check-in-inspector.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 3 · Call Every Discovery Tool In Inspector
- Estimated time: 75 minutes
- Learning purpose: how to validate inputs, outputs, and provenance without AgentGuard
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day06_lab03_call-every-discovery-tool-in-inspector.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 4 · Try Invalid Tool Inputs In Inspector
- Estimated time: 55 minutes
- Learning purpose: how errors should be clear and safe rather than leaking internals
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day06_lab04_try-invalid-tool-inputs-in-inspector.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 5 · Build The Independent Stdio Mcp Client
- Estimated time: 90 minutes
- Learning purpose: how a client starts the server, initializes a session, lists tools, and calls one
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python scripts/run_mcp_live_smoke.py`
- Prompt: `prompts/course_labs/day06_lab05_build-the-independent-stdio-mcp-client.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 6 · Validate The Server Exposed Tool Allowlist In The Client
- Estimated time: 55 minutes
- Learning purpose: how the client refuses unexpected server capabilities
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day06_lab06_validate-the-server-exposed-tool-allowlist-in-the-client.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 7 · Handle Unavailable Server And Malformed Response Errors
- Estimated time: 70 minutes
- Learning purpose: how integration failures become controlled product errors
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day06_lab07_handle-unavailable-server-and-malformed-response-errors.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 8 · Save Inspector And Client Evidence
- Estimated time: 35 minutes
- Learning purpose: how to prove protocol-level behavior during an interview
- Files: `notes/learning_log.md`, `mcp_client.py`, `mcp_server.py`, `scripts/run_mcp_live_smoke.py`, `docs/v3_inspector_walkthrough.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day06_lab08_save-inspector-and-client-evidence.txt`
- Done when: MCP Inspector starts locally and can list the five read-only AgentGuard discovery tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 1 · Define The Mcp To Agentguard Adapter Contract
- Estimated time: 55 minutes
- Learning purpose: why external schemas should not flow directly into internal business logic
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab01_define-the-mcp-to-agentguard-adapter-contract.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 2 · Validate Every Required Agent Field
- Estimated time: 65 minutes
- Learning purpose: how missing identity, tools, owner, or approval information is rejected
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab02_validate-every-required-agent-field.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 3 · Normalize The Discovered Environment
- Estimated time: 60 minutes
- Learning purpose: how the adapter produces the exact v1 scanner shape
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab03_normalize-the-discovered-environment.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 4 · Preserve Source Hash And Correlation Id
- Estimated time: 45 minutes
- Learning purpose: how provenance stays attached to the risk report
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab04_preserve-source-hash-and-correlation-id.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 5 · Scan The Mcp Discovered Inventory
- Estimated time: 60 minutes
- Learning purpose: how v1 deterministic policy remains reusable behind a new integration
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab05_scan-the-mcp-discovered-inventory.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 6 · Pass Discovered Findings Into The V2 Grounded Analyst
- Estimated time: 75 minutes
- Learning purpose: how v3 composes discovery, policy, retrieval, and explanation
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab06_pass-discovered-findings-into-the-v2-grounded-analyst.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 7 · Write Adapter Positive And Negative Tests
- Estimated time: 70 minutes
- Learning purpose: how malformed server data cannot silently enter AgentGuard
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab07_write-adapter-positive-and-negative-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 8 · Run The Complete Discovery To Analysis Flow
- Estimated time: 60 minutes
- Learning purpose: how the first end-to-end connected scenario works
- Files: `notes/learning_log.md`, `discovery_adapter.py`, `scanner.py`, `v2_service.py`, `tests/test_discovery_adapter.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_discovery_adapter.py`
- Prompt: `prompts/course_labs/day07_lab08_run-the-complete-discovery-to-analysis-flow.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 1 · Create The V3 Threat Model Attack Checklist
- Estimated time: 55 minutes
- Learning purpose: how security design begins with explicit abuse cases
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab01_create-the-v3-threat-model-attack-checklist.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 2 · Test Path Traversal And Absolute Paths
- Estimated time: 60 minutes
- Learning purpose: how `../` and `/etc/...` attempts should fail
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab02_test-path-traversal-and-absolute-paths.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 3 · Test Unapproved Filenames And Symlink Escape
- Estimated time: 65 minutes
- Learning purpose: how fixed allowlists protect even when a file exists
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab03_test-unapproved-filenames-and-symlink-escape.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 4 · Test Missing Fields Wrong Types And Oversized Names
- Estimated time: 65 minutes
- Learning purpose: how schema validation limits malformed input
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab04_test-missing-fields-wrong-types-and-oversized-names.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 5 · Test Prompt Injection As Untrusted Data
- Estimated time: 60 minutes
- Learning purpose: why the server must not turn connected text into instructions
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab05_test-prompt-injection-as-untrusted-data.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 6 · Test An Unexpected Server Tool Name
- Estimated time: 55 minutes
- Learning purpose: how clients defend against capability expansion
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab06_test-an-unexpected-server-tool-name.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 7 · Verify The Connected Files Are Byte For Byte Unchanged
- Estimated time: 50 minutes
- Learning purpose: how hashes prove v3 performed no writes
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_mcp_security.py tests/test_untrusted_content.py`
- Prompt: `prompts/course_labs/day08_lab07_verify-the-connected-files-are-byte-for-byte-unchanged.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 8 · Run And Document The V3 Security Evaluation Suite
- Estimated time: 55 minutes
- Learning purpose: how multiple controls become one release-gate artifact
- Files: `notes/learning_log.md`, `docs/v3_threat_model.md`, `mcp_security.py`, `tests/test_mcp_security.py`, `tests/test_untrusted_content.py`, `evals/run_v3_evals.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python evals/run_v3_evals.py`
- Prompt: `prompts/course_labs/day08_lab08_run-and-document-the-v3-security-evaluation-suite.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 1 · Map The V3 Streamlit Discovery Journey
- Estimated time: 45 minutes
- Learning purpose: how users initiate discovery and understand the boundary
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `streamlit run app_v3.py`
- Prompt: `prompts/course_labs/day09_lab01_map-the-v3-streamlit-discovery-journey.txt`
- Done when: The AgentGuard v3 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 2 · Create App V3 Py With Debug And Mcp Paths
- Estimated time: 75 minutes
- Learning purpose: how a direct core path helps isolate transport problems
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab02_create-app-v3-py-with-debug-and-mcp-paths.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 3 · Display Inventory Provenance And Risk Results
- Estimated time: 65 minutes
- Learning purpose: how source hashes and correlation IDs become visible evidence
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `streamlit run app_v3.py`
- Prompt: `prompts/course_labs/day09_lab03_display-inventory-provenance-and-risk-results.txt`
- Done when: The AgentGuard v3 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 4 · Add Safe Mcp Error Handling
- Estimated time: 55 minutes
- Learning purpose: how server failures are explained without exposing secrets
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab04_add-safe-mcp-error-handling.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 5 · Add Read Only Discovery Audit Events
- Estimated time: 60 minutes
- Learning purpose: how to record calls, tool names, hashes, and outcomes
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab05_add-read-only-discovery-audit-events.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 6 · Update Github Actions For V3 Tests And Evals
- Estimated time: 60 minutes
- Learning purpose: how CI proves all inherited and new behavior
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python evals/run_v3_evals.py`
- Prompt: `prompts/course_labs/day09_lab06_update-github-actions-for-v3-tests-and-evals.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 7 · Ask Claude Code For An Mcp Security Review
- Estimated time: 60 minutes
- Learning purpose: how to challenge tool scope, validation, and trust assumptions
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab07_ask-claude-code-for-an-mcp-security-review.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 8 · Resolve Findings And Create The Release Candidate
- Estimated time: 80 minutes
- Learning purpose: how to stabilize integration code before final demonstration
- Files: `notes/learning_log.md`, `app_v3.py`, `discovery_adapter.py`, `audit_log.py`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab08_resolve-findings-and-create-the-release-candidate.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 1 · Run The Complete V3 Release Gate
- Estimated time: 60 minutes
- Learning purpose: how one command proves v1, v2, and v3 tests and evaluations
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `python scripts/run_release_gate.py`
- Prompt: `prompts/course_labs/day10_lab01_run-the-complete-v3-release-gate.txt`
- Done when: The terminal ends with RELEASE GATE PASS for AgentGuard v3. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 2 · Verify The Server Exposes Exactly Five Read Only Tools
- Estimated time: 40 minutes
- Learning purpose: how source inspection and Inspector evidence support the claim
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab02_verify-the-server-exposes-exactly-five-read-only-tools.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 3 · Finalize The V3 Readme Architecture And Threat Model
- Estimated time: 80 minutes
- Learning purpose: how another engineer can reproduce the MCP integration
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`, `docs/v3_threat_model.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab03_finalize-the-v3-readme-architecture-and-threat-model.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 4 · Create Final Inspector Browser And Test Screenshots
- Estimated time: 55 minutes
- Learning purpose: how to capture protocol, product, and verification layers
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`, `app_v3.py`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `npx @modelcontextprotocol/inspector --help`
- Prompt: `prompts/course_labs/day10_lab04_create-final-inspector-browser-and-test-screenshots.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 5 · Practice The Five Minute V3 Product Demonstration
- Estimated time: 75 minutes
- Learning purpose: how to show connected discovery, provenance, policy scanning, and security controls
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab05_practice-the-five-minute-v3-product-demonstration.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 6 · Prepare Mcp And Agent Security Interview Answers
- Estimated time: 75 minutes
- Learning purpose: how to explain MCP architecture, authorization boundaries, and prompt injection
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab06_prepare-mcp-and-agent-security-interview-answers.txt`
- Done when: The current MCP 2.x contract is used; the tool set remains exactly five read-only tools. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 7 · Review Public Repository Readiness
- Estimated time: 40 minutes
- Learning purpose: how to remove secrets, local paths, and noisy artifacts
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab07_review-public-repository-readiness.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 8 · Create The V3 To V4 Governed Action Handoff
- Estimated time: 45 minutes
- Learning purpose: why v4 adds proposals and approval instead of adding a general write tool to v3
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v3_architecture.md`, `docs/v3_interview_brief.md`, `docs/v3_to_v4_handoff.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v3` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab08_create-the-v3-to-v4-governed-action-handoff.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.
