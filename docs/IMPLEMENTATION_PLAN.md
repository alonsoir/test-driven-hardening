### **📄 Documento 3: `IMPLEMENTATION_PLAN.md`**

```markdown
# Test Driven Hardening - Implementation Plan (Prototype Phase)

## Phase 0: Foundation & Setup (Week 1)
**Goal**: Barebones orchestrator that can run a single step manually.
- [ ] **Repository Structure**:
tdh-engine-prototype/
├── src/
│ ├── orchestrator.py # Core state machine
│ ├── models.py # Data classes (VulnerabilityTicket, etc.)
│ └── logging_config.py
├── tests/
├── requirements.txt
└── README.md

text
- [ ] **Basic `VulnerabilityTicket` class** with state enum for the 7 steps.
- [ ] **Simple file-based persistence** (JSON) for tickets.
- [ ] **Logging** structured to track step transitions.

## Phase 1: Single-Agent Validation (Week 2)
**Goal**: Automate Steps 1 & 2 with a single "Master" LLM (e.g., DeepSeek).
- [ ] **`LLMCouncilClient` basic implementation** for one provider.
- [ ] **Prompt templates** for Step 1 (Create PoC) and Step 3 (Initial Hypothesis).
- [ ] **`TestBuildRunner`** to execute simple shell commands in a temporary directory.
- [ ] **Integration test**: Feed a trivial SAST finding (e.g., "potential buffer overflow in dummy.c") and verify the PoC is generated.

## Phase 2: Multi-Agent Workspace Orchestration (Week 3)
**Goal**: Implement Steps 3 & 4 (Council validation).
- [ ] **`WorkspaceManager`** to create N isolated directories from a source repo.
- [ ] Extend `Orchestrator` to distribute hypothesis and PoC to workspaces.
- [ ] **`TestBuildRunner`** to run validation in each workspace and collect results.
- [ ] **Consensus check**: Require all agents to confirm reproduction before proceeding.

## Phase 3: Fix Generation & Empirical Selection (Week 4)
**Goal**: Implement Steps 5, 6 & 7 (The core of TDH).
- [ ] **Prompt template** for Step 5 (Fix hypothesis generation).
- [ ] **`Orchestrator` logic** to apply each proposed fix to respective workspaces.
- [ ] **`TestBuildRunner`** to compile and run PoC (must pass) and any existing test suite.
- [ ] **`ConsensusEngine` basic version** to rank fixes based on success and a simplicity heuristic.

## Phase 4: Artifact Generation & CI Integration (Week 5)
**Goal**: Close the loop and produce usable outputs.
- [ ] **`ArtifactGenerator`** to create:
    - A diff patch for the selected fix.
    - A minimal `HardeningJournal` entry (JSON).
    - A summary markdown report.
- [ ] **Basic CI example**: A script that simulates a GitHub Action calling the TDH engine.

## Phase 5: From Prototype to Engine
**Goal**: Evaluate, refine, and plan the C++ core.
- [ ] **Benchmark & Profile**: Identify bottlenecks (likely workspace ops and LLM calls).
- [ ] **Define C++ Core Interface**: Precisely specify the API of `Orchestrator` and `WorkspaceManager` for C++ port.
- [ ] **Spike a C++ Module**: Port the `WorkspaceManager` to C++ as a proof-of-concept, called from Python via `ctypes` or `pybind11`.

## Development Principles
- **Test-First for Logic**: Unit test the state machine and algorithms heavily.
- **Integration Tests with Mocks**: Use mock LLM responses and simulated repos for CI.
- **Configuration over Hardcoding**: All model choices, API keys, timeouts, paths should be configurable via a file or env vars.