# Test Driven Hardening (TDH) - Architecture Design
*Version 0.1 - Prototype-First, C++-Ready*

## Design Philosophy
- **Prototype in Python**: Leverage rapid development and rich LLM/ML ecosystem.
- **Production path to C++**: Core, performance-critical components (orchestrator, workspace mgr) designed for eventual porting.
- **Clear Interfaces**: Define contracts between components to allow language-agnostic replacement.
- **Stateful Orchestration**: The engine maintains state for each vulnerability through the 7-step lifecycle.

## High-Level Component Architecture
[SAST Tool] → [TDH Engine Orchestrator] → [Fixed Code + Artifacts]
|
├── Workspace Manager
├── LLM Council Client
├── Test & Build Runner
├── Consensus Engine
└── Artifact Generator

text

### Core Components (Python Prototype / Future C++ Core)

#### 1. `Orchestrator` (Brain)
- **Responsibility**: Main state machine driving the 7-step process.
- **State**: Tracks `VulnerabilityTicket`: ID, status (step), assigned agents, PoC path, fix candidates, consensus results.
- **Interface (Planned for C++)**:
```cpp
class Orchestrator {
public:
    VulnerabilityTicket process_finding(const SastFinding& finding);
    void execute_step(VulnerabilityTicket& ticket, ProcessStep step);
};
2. WorkspaceManager (Sandbox)

Responsibility: Creates isolated, ephemeral workspaces for each LLM agent.
Action: Forks repository, applies initial state, manages cleanup.
Key Challenge: Efficient copy-on-write for large repos (consider git worktree or copy).
Python Proto: Use tempfile.mkdtemp() + shutil.copytree() + subprocess for git.
C++ Future: Direct system calls, efficient file I/O.
3. LLMCouncilClient (Diplomat)

Responsibility: Communicates with various LLM APIs (OpenAI, Anthropic, DeepSeek, etc.) with specialized prompts per step.
Abstraction: Unified LLMProvider interface to swap models.
Python Proto: Libraries like openai, anthropic, httpx.
Prompt Strategy: Each step (3, 5, 7) has a dedicated prompt template injecting context (code, PoC, error logs).
4. TestBuildRunner (Empirical Validator)

Responsibility: Executes commands in agent workspaces: run PoC, apply fix, compile, test.
Interface: run_command(workspace_path, command[], timeout) -> ExecutionResult.
Critical: Must capture stdout/stderr, exit codes, and timeouts robustly.
Python Proto: subprocess.run with comprehensive logging.
5. ConsensusEngine (Judge)

Responsibility: Implements anonymous ranking and final fix selection based on criteria (correctness, minimalism, elegance).
Algorithm: Adapted from llm-council (anonymous review + ranking), extended with empirical result weighting (e.g., fix that passes tests in all workspaces gets higher score).
6. ArtifactGenerator (Scribe)

Responsibility: Creates final outputs: Pull Request diff, Hardening Journal entry (JSON), summary report.
Outputs: Structured data for CI/CD integration.
Data Flow & State Lifecycle

Ticket Creation: Orchestrator creates a VulnerabilityTicket from SAST finding.
Step 1-2 (PoC): Orchestrator → LLMCouncilClient (Master) → TestBuildRunner (validate PoC).
Step 3-4 (Hypothesis): WorkspaceManager creates N workspaces → LLMCouncilClient distributes hypothesis → TestBuildRunner validates reproduction.
Step 5-7 (Fix): LLMCouncilClient gathers fix hypotheses → TestBuildRunner validates each → ConsensusEngine selects best → ArtifactGenerator produces output.
State Persistence: Ticket state saved to disk (JSON) after each step for crash recovery.
Key Technical Decisions for Prototype

Concurrency: Use asyncio for parallel LLM API calls and workspace operations. Limit concurrent workspaces based on system resources.
Security: Workspaces must be fully isolated (containerization? chroot? For prototype, separate user dirs may suffice).
Idempotency: Each step should be retryable. Workspace creation is deterministic from ticket ID and step.
Path to C++ Production Engine

The prototype validates the process and algorithms. The C++ port focuses on:

Performance: Replace Python Orchestrator and WorkspaceManager with C++ for speed and lower overhead.
Robustness: Better system resource control, sandboxing (e.g., namespace/cgroups).
Integration: Direct linking with C++ SAST tools or codebases (like ML Defender).
Python Compatibility: Keep LLMCouncilClient and ConsensusEngine in Python initially, call via C++ bindings (pybind11) if needed, as they are less performance-critical.