# AgentGuard v4 Lab Execution Index

This is the reviewed, authoritative map between the manual, the starter-kit files, and the exact Claude Code prompt for every lab.

> Use the manual for teaching and click-by-click guidance. Use the matching prompt file for Claude Code. The file and command list below has been validated against this starter kit.

## Day 1 · Lab 1 · Understand The V4 Problem And Finish Line
- Estimated time: 55 minutes
- Learning purpose: why finding risk is not enough and why autonomous remediation is dangerous
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab01_understand-the-v4-problem-and-finish-line.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 2 · Copy The Released V3 Project Into A New V4 Folder
- Estimated time: 35 minutes
- Learning purpose: how to preserve the read-only integration as the trusted discovery baseline
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer` ; `cp -R agentguard-v3 agentguard-v4` ; `cd agentguard-v4` ; `pwd`
- Prompt: `prompts/course_labs/day01_lab02_copy-the-released-v3-project-into-a-new-v4-folder.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 3 · Open The Project In All Working Tools
- Estimated time: 40 minutes
- Learning purpose: how code, Terminal, browser, GitHub, and Docker will be used
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab03_open-the-project-in-all-working-tools.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 4 · Create The V4 Branch And Baseline Commit
- Estimated time: 40 minutes
- Learning purpose: how to isolate action-layer changes
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab04_create-the-v4-branch-and-baseline-commit.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 5 · Run All V1 V3 Release Gates
- Estimated time: 55 minutes
- Learning purpose: how to prove remediation starts from a stable discovery and analysis platform
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `scripts/run_release_gate.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python scripts/run_release_gate.py`
- Prompt: `prompts/course_labs/day01_lab05_run-all-v1-v3-release-gates.txt`
- Done when: The terminal ends with RELEASE GATE PASS for AgentGuard v4. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 6 · Learn Proposal Diff Hash Approval Verification Pr And Rollba
- Estimated time: 90 minutes
- Learning purpose: the concepts required for safe agentic action
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `approval.py`, `proposal_hash.py`, `tests/test_approval.py`, `tests/test_proposal_hash.py`, `verifier.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_approval.py tests/test_proposal_hash.py tests/test_verifier.py`
- Prompt: `prompts/course_labs/day01_lab06_learn-proposal-diff-hash-approval-verification-pr-and-rollba.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 7 · Draw The V4 State Machine And Trust Boundaries
- Estimated time: 70 minutes
- Learning purpose: how data and authority change at each state
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `docs/v4_architecture.md`, `workflow.py`, `tests/test_workflow.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py`
- Prompt: `prompts/course_labs/day01_lab07_draw-the-v4-state-machine-and-trust-boundaries.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 1 · Lab 8 · Create Day 1 Evidence And A No Production Pledge
- Estimated time: 35 minutes
- Learning purpose: how to document that the MVP uses only synthetic repositories and draft changes
- Files: `notes/learning_log.md`, `README.md`, `START_HERE.md`, `VERSION.txt`, `CLAUDE.md`, `docs/roadmap.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day01_lab08_create-day-1-evidence-and-a-no-production-pledge.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 1 · Understand Github Repository Branch Commit Push Pull Request
- Estimated time: 70 minutes
- Learning purpose: how source-control review separates a proposal from an applied production change
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`, `github_plan.py`, `tests/test_github_plan.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day02_lab01_understand-github-repository-branch-commit-push-pull-request.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 2 · Install And Verify Github Cli
- Estimated time: 40 minutes
- Learning purpose: how `gh` provides controlled command-line access to GitHub
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `brew install gh` ; `gh --version`
- Prompt: `prompts/course_labs/day02_lab02_install-and-verify-github-cli.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 3 · Authenticate Github Cli Through The Browser
- Estimated time: 45 minutes
- Learning purpose: how OAuth login avoids placing a token in project files
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`, `app_v4.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `gh auth login` ; `gh auth status`
- Prompt: `prompts/course_labs/day02_lab03_authenticate-github-cli-through-the-browser.txt`
- Done when: The AgentGuard v4 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 4 · Create A Separate Private Remediation Demo Repository
- Estimated time: 55 minutes
- Learning purpose: why the training workflow must never target the AgentGuard source repository or production code
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab04_create-a-separate-private-remediation-demo-repository.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 5 · Clone The Demo Repository And Add Synthetic Agent Data
- Estimated time: 60 minutes
- Learning purpose: how a safe target repository represents a configuration change
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day02_lab05_clone-the-demo-repository-and-add-synthetic-agent-data.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 6 · Add A Pull Request Template And Branch Naming Rule
- Estimated time: 55 minutes
- Learning purpose: how review metadata standardizes proposed changes
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`, `github_plan.py`, `tests/test_github_plan.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day02_lab06_add-a-pull-request-template-and-branch-naming-rule.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 7 · Practice A Manual Draft Pull Request And Close It
- Estimated time: 75 minutes
- Learning purpose: how to understand the human workflow before AgentGuard automates it
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`, `github_plan.py`, `tests/test_github_plan.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day02_lab07_practice-a-manual-draft-pull-request-and-close-it.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 2 · Lab 8 · Record Repository Allowlist Values Without Secrets
- Estimated time: 40 minutes
- Learning purpose: how owner/repo, file path, and branch prefix become configuration
- Files: `notes/learning_log.md`, `docs/v4_github_demo_setup.md`, `.gitignore`, `CLAUDE.md`, `scripts/check_no_secrets.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python scripts/check_no_secrets.py`
- Prompt: `prompts/course_labs/day02_lab08_record-repository-allowlist-values-without-secrets.txt`
- Done when: The secret scanner prints SECRET CHECK PASS and no API key is committed. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 1 · Understand Why Arbitrary Ai Generated Patches Are Excluded
- Estimated time: 60 minutes
- Learning purpose: how unconstrained code generation creates an unacceptable action surface
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab01_understand-why-arbitrary-ai-generated-patches-are-excluded.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 2 · Define The Three Allowlisted Remediation Templates
- Estimated time: 55 minutes
- Learning purpose: how human approval, owner assignment, and broad-tool removal address v1 findings
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab02_define-the-three-allowlisted-remediation-templates.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 3 · Create The Remediationproposal Data Contract
- Estimated time: 65 minutes
- Learning purpose: how proposals describe intent, target, changes, rationale, and source hash
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab03_create-the-remediationproposal-data-contract.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 4 · Implement Require Human Approval
- Estimated time: 60 minutes
- Learning purpose: how one deterministic field change mitigates high-impact autonomous actions
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`, `approval.py`, `proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day03_lab04_implement-require-human-approval.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 5 · Implement Assign Owner With Required Input
- Estimated time: 60 minutes
- Learning purpose: how user-supplied values are validated before proposal creation
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab05_implement-assign-owner-with-required-input.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 6 · Implement Remove Broad Admin Tool
- Estimated time: 65 minutes
- Learning purpose: how an allowlisted transformation removes wildcard and administrator tools
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab06_implement-remove-broad-admin-tool.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 7 · Apply Proposals To Deep Copies Only
- Estimated time: 55 minutes
- Learning purpose: how the original source remains unchanged during planning
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab07_apply-proposals-to-deep-copies-only.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 3 · Lab 8 · Write Template And Immutability Tests
- Estimated time: 75 minutes
- Learning purpose: how tests prove only approved templates and fields can change
- Files: `notes/learning_log.md`, `remediation_templates.py`, `tests/test_remediation_templates.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_remediation_templates.py`
- Prompt: `prompts/course_labs/day03_lab08_write-template-and-immutability-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 1 · Understand Canonical Json And Sha 256
- Estimated time: 65 minutes
- Learning purpose: how identical structured data produces a stable fingerprint
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab01_understand-canonical-json-and-sha-256.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 2 · Build Canonical Json And Sha256 Value Helpers
- Estimated time: 60 minutes
- Learning purpose: how sorting keys and fixed separators prevent accidental hash variation
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab02_build-canonical-json-and-sha256-value-helpers.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 3 · Hash The Exact Source Environment
- Estimated time: 50 minutes
- Learning purpose: how approval can be tied to what was reviewed
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab03_hash-the-exact-source-environment.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 4 · Hash The Complete Remediation Proposal
- Estimated time: 50 minutes
- Learning purpose: how a changed target, field, or value invalidates old approval
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab04_hash-the-complete-remediation-proposal.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 5 · Create The Approvalrecord Data Contract
- Estimated time: 60 minutes
- Learning purpose: how reviewer, decision, reason, time, and hashes become audit evidence
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab05_create-the-approvalrecord-data-contract.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 6 · Implement Approve And Reject Decisions
- Estimated time: 60 minutes
- Learning purpose: how the product records an explicit human choice
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab06_implement-approve-and-reject-decisions.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 7 · Reject Changed Proposal And Changed Source Hashes
- Estimated time: 65 minutes
- Learning purpose: how stale approval is blocked automatically
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab07_reject-changed-proposal-and-changed-source-hashes.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 4 · Lab 8 · Write Exact Approval And Stale Approval Tests
- Estimated time: 70 minutes
- Learning purpose: how negative tests prove approval cannot be replayed
- Files: `notes/learning_log.md`, `proposal_hash.py`, `approval.py`, `tests/test_proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_proposal_hash.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day04_lab08_write-exact-approval-and-stale-approval-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 1 · Understand Workflow States And Terminal States
- Estimated time: 60 minutes
- Learning purpose: why a safe process must know whether it is discovered, proposed, approved, or verified
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab01_understand-workflow-states-and-terminal-states.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 2 · Define The V4 State List And Transition Map
- Estimated time: 60 minutes
- Learning purpose: how an allowlist applies to process movement as well as tools
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab02_define-the-v4-state-list-and-transition-map.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 3 · Implement Transition Validation
- Estimated time: 55 minutes
- Learning purpose: how state skipping becomes a clear error
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab03_implement-transition-validation.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 4 · Design The Sqlite Workflow Events Table
- Estimated time: 60 minutes
- Learning purpose: how a local relational database preserves ordered event history
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab04_design-the-sqlite-workflow-events-table.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 5 · Implement Database Initialization And Event Writes
- Estimated time: 70 minutes
- Learning purpose: how every transition becomes durable evidence
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab05_implement-database-initialization-and-event-writes.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 6 · Implement Ordered Event Retrieval
- Estimated time: 50 minutes
- Learning purpose: how a reviewer reconstructs what happened
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python evals/run_v4_evals.py`
- Prompt: `prompts/course_labs/day05_lab06_implement-ordered-event-retrieval.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 7 · Write State Skip And Event Order Tests
- Estimated time: 65 minutes
- Learning purpose: how tests prove the control flow cannot jump ahead
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab07_write-state-skip-and-event-order-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 5 · Lab 8 · Inspect The Audit Database With Python
- Estimated time: 55 minutes
- Learning purpose: how to view rows without needing a separate database application
- Files: `notes/learning_log.md`, `workflow.py`, `audit_db.py`, `tests/test_workflow.py`, `tests/test_audit_db.py`, `docs/v4_state_machine.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_workflow.py tests/test_audit_db.py`
- Prompt: `prompts/course_labs/day05_lab08_inspect-the-audit-database-with-python.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 1 · Understand Verification Versus Approval
- Estimated time: 55 minutes
- Learning purpose: why a human can approve intent while software still checks correctness
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`, `approval.py`, `proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day06_lab01_understand-verification-versus-approval.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 2 · Create An Isolated Temporary Verification Directory
- Estimated time: 55 minutes
- Learning purpose: how temporary files prevent direct modification of the source
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab02_create-an-isolated-temporary-verification-directory.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 3 · Apply The Proposal Only To The Isolated Candidate
- Estimated time: 60 minutes
- Learning purpose: how candidate state is produced for testing
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab03_apply-the-proposal-only-to-the-isolated-candidate.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 4 · Rescan Before And After Risk Results
- Estimated time: 65 minutes
- Learning purpose: how remediation must not increase the high-risk count
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab04_rescan-before-and-after-risk-results.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 5 · Add Structural And Serialization Checks
- Estimated time: 55 minutes
- Learning purpose: how to catch malformed candidate data
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab05_add-structural-and-serialization-checks.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 6 · Add Target Count And Allowlisted Key Checks
- Estimated time: 55 minutes
- Learning purpose: how verification ensures the proposal touched exactly one intended object
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab06_add-target-count-and-allowlisted-key-checks.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 7 · Create A Detailed Verificationresult
- Estimated time: 55 minutes
- Learning purpose: how pass/fail evidence is displayed and audited
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab07_create-a-detailed-verificationresult.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 6 · Lab 8 · Write Verifier Positive And Failure Tests
- Estimated time: 75 minutes
- Learning purpose: how a proposal cannot advance when any required check fails
- Files: `notes/learning_log.md`, `verifier.py`, `scanner.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_verifier.py`
- Prompt: `prompts/course_labs/day06_lab08_write-verifier-positive-and-failure-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 1 · Define Repository Branch And File Path Allowlists
- Estimated time: 60 minutes
- Learning purpose: how configuration prevents command injection and wrong-target changes
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab01_define-repository-branch-and-file-path-allowlists.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 2 · Create The Githubplan Data Contract
- Estimated time: 55 minutes
- Learning purpose: how exact commands become reviewable data before execution
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab02_create-the-githubplan-data-contract.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 3 · Build Safe Branch And Commit Commands
- Estimated time: 65 minutes
- Learning purpose: how a remediation is isolated from main
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab03_build-safe-branch-and-commit-commands.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 4 · Build The Draft Pull Request Command
- Estimated time: 55 minutes
- Learning purpose: how `--draft` guarantees the change begins in review state
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab04_build-the-draft-pull-request-command.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 5 · Implement Dry Run Execution As The Default
- Estimated time: 60 minutes
- Learning purpose: how users can inspect every command without changing GitHub
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab05_implement-dry-run-execution-as-the-default.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 6 · Add Explicit Opt In Live Execution
- Estimated time: 60 minutes
- Learning purpose: how action authority is separated from plan generation
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab06_add-explicit-opt-in-live-execution.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 7 · Block Unapproved Repositories Paths And Branch Names
- Estimated time: 60 minutes
- Learning purpose: how input validation protects the command boundary
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab07_block-unapproved-repositories-paths-and-branch-names.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 7 · Lab 8 · Write Draft Only And Dry Run Automated Tests
- Estimated time: 70 minutes
- Learning purpose: how tests prove there is no merge or main-branch command
- Files: `notes/learning_log.md`, `github_plan.py`, `tests/test_github_plan.py`, `docs/v4_github_demo_setup.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day07_lab08_write-draft-only-and-dry-run-automated-tests.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 1 · Understand Rollback Before And After Merge
- Estimated time: 55 minutes
- Learning purpose: why closing a draft is simple but undoing a merged change requires a reviewed revert
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py`
- Prompt: `prompts/course_labs/day08_lab01_understand-rollback-before-and-after-merge.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 2 · Create The Pre Merge Rollback Command Plan
- Estimated time: 55 minutes
- Learning purpose: how to close a pull request and delete its branch
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py`
- Prompt: `prompts/course_labs/day08_lab02_create-the-pre-merge-rollback-command-plan.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 3 · Refuse Automatic Rollback After Merge
- Estimated time: 50 minutes
- Learning purpose: how the product avoids silently changing shared history
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py`
- Prompt: `prompts/course_labs/day08_lab03_refuse-automatic-rollback-after-merge.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 4 · Record Rejected Failed And Rolled Back Terminal States
- Estimated time: 60 minutes
- Learning purpose: how the audit trail remains complete when work does not succeed
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`, `tests/test_workflow.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py tests/test_workflow.py`
- Prompt: `prompts/course_labs/day08_lab04_record-rejected-failed-and-rolled-back-terminal-states.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 5 · Simulate Verification Failure
- Estimated time: 55 minutes
- Learning purpose: how a failed check stops GitHub planning
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`, `verifier.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py tests/test_verifier.py`
- Prompt: `prompts/course_labs/day08_lab05_simulate-verification-failure.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 6 · Simulate Stale Approval
- Estimated time: 55 minutes
- Learning purpose: how changed data forces a new human review
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`, `approval.py`, `proposal_hash.py`, `tests/test_approval.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py tests/test_approval.py`
- Prompt: `prompts/course_labs/day08_lab06_simulate-stale-approval.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 7 · Simulate Github Authentication And Command Failure
- Estimated time: 65 minutes
- Learning purpose: how external-system errors are surfaced without partial continuation
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py tests/test_failure_paths.py`
- Prompt: `prompts/course_labs/day08_lab07_simulate-github-authentication-and-command-failure.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 8 · Lab 8 · Run The V4 Failure Injection Evaluation
- Estimated time: 60 minutes
- Learning purpose: how negative scenarios prove the system fails closed
- Files: `notes/learning_log.md`, `rollback.py`, `workflow.py`, `evals/run_v4_evals.py`, `tests/test_rollback.py`, `tests/test_failure_paths.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python evals/run_v4_evals.py`
- Prompt: `prompts/course_labs/day08_lab08_run-the-v4-failure-injection-evaluation.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 1 · Map The V4 Streamlit User Journey
- Estimated time: 50 minutes
- Learning purpose: how discovery, proposal, approval, verification, plan, and audit are shown in order
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `streamlit run app_v4.py`
- Prompt: `prompts/course_labs/day09_lab01_map-the-v4-streamlit-user-journey.txt`
- Done when: The AgentGuard v4 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 2 · Create App V4 Py Input And Proposal Controls
- Estimated time: 75 minutes
- Learning purpose: how the user selects an agent and one allowlisted template
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab02_create-app-v4-py-input-and-proposal-controls.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 3 · Display Hashes Approval Verification And Events
- Estimated time: 65 minutes
- Learning purpose: how the UI makes invisible control evidence visible
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`, `approval.py`, `proposal_hash.py`, `tests/test_approval.py`, `tests/test_proposal_hash.py`, `verifier.py`, `tests/test_verifier.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_approval.py tests/test_proposal_hash.py tests/test_verifier.py`
- Prompt: `prompts/course_labs/day09_lab03_display-hashes-approval-verification-and-events.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 4 · Display The Github Dry Run Plan And Safety Warnings
- Estimated time: 55 minutes
- Learning purpose: how users review exact actions before enabling live execution
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `streamlit run app_v4.py`
- Prompt: `prompts/course_labs/day09_lab04_display-the-github-dry-run-plan-and-safety-warnings.txt`
- Done when: The AgentGuard v4 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 5 · Install Docker Desktop And Verify Docker Commands
- Estimated time: 60 minutes
- Learning purpose: how containers package Python and dependencies consistently
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `docker --version` ; `docker compose version` ; `docker info`
- Prompt: `prompts/course_labs/day09_lab05_install-docker-desktop-and-verify-docker-commands.txt`
- Done when: Docker reports healthy commands or the AgentGuard container starts in mock/dry-run mode. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 6 · Create Dockerfile Dockerignore And Compose Yaml
- Estimated time: 80 minutes
- Learning purpose: how the application becomes a reproducible local service without including secrets
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab06_create-dockerfile-dockerignore-and-compose-yaml.txt`
- Done when: Docker reports healthy commands or the AgentGuard container starts in mock/dry-run mode. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 7 · Build And Run The Container In Mock And Dry Run Mode
- Estimated time: 75 minutes
- Learning purpose: how to test the packaged product at localhost
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab07_build-and-run-the-container-in-mock-and-dry-run-mode.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 9 · Lab 8 · Update Ci And Ask Claude Code For A Final Security Review
- Estimated time: 80 minutes
- Learning purpose: how all versions remain tested and the action boundary is challenged
- Files: `notes/learning_log.md`, `app_v4.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `.github/workflows/tests.yml`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day09_lab08_update-ci-and-ask-claude-code-for-a-final-security-review.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 1 · Run The Complete V4 Release Gate
- Estimated time: 70 minutes
- Learning purpose: how one command proves all inherited and v4 controls
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python scripts/run_release_gate.py`
- Prompt: `prompts/course_labs/day10_lab01_run-the-complete-v4-release-gate.txt`
- Done when: The terminal ends with RELEASE GATE PASS for AgentGuard v4. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 2 · Run The Full Local Browser Scenario
- Estimated time: 60 minutes
- Learning purpose: how a finding becomes a verified proposal and dry-run plan
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`, `app_v4.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `streamlit run app_v4.py`
- Prompt: `prompts/course_labs/day10_lab02_run-the-full-local-browser-scenario.txt`
- Done when: The AgentGuard v4 page opens locally and the new control or result is visible. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 3 · Optionally Create One Draft Pull Request In The Demo Reposit
- Estimated time: 75 minutes
- Learning purpose: how to perform the only live write action with explicit review and no merge
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`, `github_plan.py`, `tests/test_github_plan.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_github_plan.py`
- Prompt: `prompts/course_labs/day10_lab03_optionally-create-one-draft-pull-request-in-the-demo-reposit.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 4 · Demonstrate Rollback Of The Unmerged Draft
- Estimated time: 55 minutes
- Learning purpose: how to close the loop safely
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`, `rollback.py`, `tests/test_rollback.py`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `python -m pytest -q tests/test_rollback.py`
- Prompt: `prompts/course_labs/day10_lab04_demonstrate-rollback-of-the-unmerged-draft.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 5 · Finalize Readme Architecture Threat Model And Test Report
- Estimated time: 90 minutes
- Learning purpose: how documentation turns code into an enterprise product case study
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab05_finalize-readme-architecture-threat-model-and-test-report.txt`
- Done when: pytest reports passed tests and no failed tests for the behavior changed in this lab. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 6 · Create The Final Evidence Package And Five Minute Video Plan
- Estimated time: 75 minutes
- Learning purpose: how to show the system without exposing credentials
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab06_create-the-final-evidence-package-and-five-minute-video-plan.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 7 · Prepare Deep Technical And Product Interview Answers
- Estimated time: 90 minutes
- Learning purpose: how to explain identity, policy, MCP, RAG, guardrails, approvals, verification, audit, and rollback
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab07_prepare-deep-technical-and-product-interview-answers.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.

## Day 10 · Lab 8 · Define Post Mvp Backlog And Job Search Integration
- Estimated time: 60 minutes
- Learning purpose: how the completed prototype supports resume, LinkedIn, portfolio, and targeted interviews
- Files: `notes/learning_log.md`, `scripts/run_release_gate.py`, `scripts/validate_starter_kit.py`, `README.md`, `START_HERE.md`, `docs/v4_architecture.md`, `docs/v4_threat_model.md`, `docs/final_mvp_interview_brief.md`, `docs/post_mvp_backlog.md`, `evidence/README.md`
- Commands: `cd ~/Developer/agentguard-v4` ; `source .venv/bin/activate` ; `git status --short`
- Prompt: `prompts/course_labs/day10_lab08_define-post-mvp-backlog-and-job-search-integration.txt`
- Done when: The named files exist in the exact paths, the command completes without an unhandled error, and git shows only the expected changes. You can explain the input, processing, output, safety boundary, and reason this lab exists.
