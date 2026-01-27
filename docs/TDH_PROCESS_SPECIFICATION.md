# Test Driven Hardening: Process Specification
*Version 1.0 - Based on empirical refinement from ML Defender ISSUE-003*

## Overview
This document specifies the complete 7-step automated workflow for Test Driven Hardening (TDH). Each security finding progresses through this evidence-based, scientific methodology to ensure fixes are empirically validated before integration.

## Phase 1: Problem Discovery & Validation
### Step 1: Vulnerability Demonstration
**Input**: SAST finding (location, type, severity)  
**Action**: The **Master LLM** (first to detect issue) must produce a **minimal, reproducible proof-of-concept (PoC)** demonstrating exploitability.  
**Output**: Executable test (C++, Python, Bash, etc.) that consistently fails, proving the vulnerability exists.  
**Quality Gate**: PoC must compile/run successfully and clearly show the security impact.

### Step 2: Criticality Assessment
**Input**: SAST severity + PoC impact analysis  
**Action**: Engine calculates **exploitability score** considering: attack vector, complexity, privileges required, user interaction, scope.  
**Output**: Prioritized vulnerability queue with confidence score.

## Phase 2: Hypothesis Formation & Consensus
### Step 3: Initial Hypothesis
**Input**: Vulnerability details + PoC  
**Action**: Master LLM analyzes root cause and formulates **initial hypothesis** (e.g., "Race condition due to thread_local in producer-consumer pattern").  
**Output**: Technical hypothesis with code locations and suggested investigation path.

### Step 4: Council Validation & Reproduction
**Input**: Hypothesis + PoC + repository access  
**Action**: 
1. Engine creates **isolated workspace fork** for each council LLM
2. Each agent independently: clones, builds, runs PoC to verify failure
3. Any reproduction issues → flagged for Master LLM review
**Output**: Binary result from each agent: ✅ PoC fails (vulnerability confirmed) or ❌ Cannot reproduce. **Unanimous confirmation required to proceed**.

## Phase 3: Solution Development & Selection
### Step 5: Fix Hypothesis Generation
**Input**: Confirmed vulnerability + code context  
**Action**: Each council member proposes: **root cause analysis** + **fix strategy** + **implementation approach**.  
**Output**: N proposed fixes with technical rationale, complexity assessment, and potential side effects.

### Step 6: Fix Application & Empirical Testing
**Action**:
1. Engine applies each proposed fix to respective workspace forks
2. Each agent: compiles code, runs original PoC test (must now **pass**), runs existing test suite
3. Agents report: compilation success, PoC result, test suite results, performance metrics
**Output**: Validation matrix for each fix across all agents.

### Step 7: Consensus Fix Selection
**Criteria for "Best Fix"**:
1. **Correctness**: Resolves vulnerability without ambiguity (all agents' PoCs pass)
2. **Minimalism**: No unnecessary dependencies, minimal complexity increase
3. **Elegance**: "Evidente y bella" – clear, readable, maintainable solution
4. **Safety**: No introduced regressions (existing tests pass)
5. **Performance**: Acceptable performance profile (measured if applicable)

**Action**: Council deliberates (anonymous ranking) → Engine selects optimal fix → Generates final artifact.

## Phase 4: Artifact Generation & Integration
**Final Outputs**:
1. **Pull Request**: With fix code, PoC test (failing before, passing after), documentation
2. **Hardening Journal Entry**: Complete record: hypothesis → PoC → debate → fix → validation
3. **CVE Context Linkage**: Connection to relevant CVE patterns for institutional learning

## Implementation Notes
- **Agent Diversity**: Council should include: security specialists, language experts, systems architects
- **Fallback Mechanisms**: If consensus fails, expand council size or escalate to human oversight
- **Telemetry Collection**: Each step timed, success rates tracked for continuous improvement