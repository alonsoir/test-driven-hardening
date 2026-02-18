# TDH Engine — Deterministic Orchestrator Action Plan

## Objective

Build a deterministic manager (orchestrator) that allows LLM SOTA agents to safely analyze, reproduce, and fix vulnerabilities inside isolated repositories without human interaction.

The manager is the only component allowed to execute commands. Models only propose actions.

---

## Core Principle

The system is not an autonomous coding agent.
It is a transactional experimentation runtime over source code.

Models propose.
Manager validates, executes, records, and reverts.

---

## Phase 1 — Deterministic Single‑Model Loop (Mandatory First Goal)

Goal: Fully automatic cycle using ONE model and ONE bug.
No multi‑model logic yet.

### Required Tools (only 5 initially)

1. read_file
2. search (grep-like)
3. write_file (with backup)
4. compile
5. run_binary

If this phase is not stable → stop development. Do not add features.

---

## System Components

### 1. Manager (Central Process)

Responsibilities:

* Clone repository
* Create container per agent
* Create worktree per agent
* Execute tools requested by model
* Maintain state machine
* Handle backups and rollback
* Run tests and compilation
* Provide structured results back to model
* Record experiment history

The manager is the only executor of shell commands.

Models never directly access the system.

---

### 2. Agent (LLM SOTA)

The agent produces structured action requests.
It never executes anything.

Example action request:
{
"action": "write_file",
"path": "src/parser.cpp",
"content": "...",
"backup": true
}

Manager validates → executes → returns structured result.

---

### 3. Container Environment

Each agent has:

* Dedicated container
* Dedicated worktree
* No network access
* CPU/RAM limits
* Execution timeout

Filesystem is never shared between agents.

---

## Transactional State Machine

Every attempt is a reversible transaction.

STATE_N
-> model proposes change
-> manager applies change (creates backup)
-> compile
-> run test
-> collect result
-> if failure: rollback
-> return to STATE_N

No corrupted state can persist.

---

## Required Manager Subsystems

### Workspace Controller

* Create worktrees
* Reset to clean state
* Snapshot revision hashes

### Backup Engine

* Automatic backup before modification
* Restore on failure
* Track modified files list

### Tool Executor

Allowed commands only through controlled wrappers:

* read_file
* search
* write_file
* compile
* run_binary

All outputs normalized to structured JSON.

### Result Interpreter

Convert raw execution into structured response:

* success/failure
* compiler errors
* runtime errors
* stdout/stderr
* exit code

### State Tracker

For each attempt store:

* diff
* result
* duration
* files touched
* reproducibility

---

## Model Interaction Protocol

Loop:

1. Manager sends context
2. Model returns action JSON
3. Manager executes
4. Manager returns structured result
5. Repeat

No natural language execution instructions allowed.
Only structured actions.

---

## Success Criteria (Phase 1 Complete)

The system automatically:

1. Reads code
2. Locates bug
3. Creates reproducible test
4. Compiles test
5. Test fails (bug proven)
6. Generates fix
7. Compiles fix
8. Test passes

Without human intervention.

---

## Phase 2 — Multi‑Model Competition (Future)

(Not to be implemented yet)

Manager responsibilities later:

* Share discovered tests
* Validate reproducibility
* Compare fixes
* Produce candidate pull requests

This stage only begins after Phase 1 is reliable.

---

## Non‑Goals (For Now)

* No parallel models
* No scoring systems
* No voting
* No ranking
* No advanced tools
* No internet access

Simplicity first. Determinism first.

---

## Immediate Next Tasks

1. Define action JSON schema
2. Implement manager execution loop
3. Implement file backup system
4. Implement compile/run wrappers
5. Run on one known C++ bug until stable

Only after stability → expand capabilities.

---

## Guiding Rule

If a human is needed during the loop, the system is not finished.
