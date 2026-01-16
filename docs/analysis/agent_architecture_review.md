# Architecture Analysis: Agent System Refactor

**Source Document**: `docs/agent_architecture.md`
**Date**: 2026-01-16
**Context**: Re-alignment of User Story #77 (Structured Agent Outputs) with the broader VALOR architecture.

## 1. Core Architectural Insights

From the review of `docs/agent_architecture.md`, the following non-negotiable principles were derived:

### A. Agents as Cognitive Modules, Not Services
*   **Insight**: Agents are internal libraries (`app.agent`), not independent microservices behind APIs.
*   **Implication**: We must not expose agents via individual API endpoints. There is only one Gateway.
*   **Correction**: Previous thoughts of "chaining agents" via HTTP or messy internal calls are replaced by strict **Orchestrator** patterns.

### B. The Output Contract (Strict & Ephemeral)
*   **Insight**: Communication between backend and frontend must use a "Score" (Partituur). Agents produce *Artifacts*, not UI components or direct Database changes.
*   **Implication**: `AgentOutput` must be a strictly typed Pydantic object (the "Artifact").
*   **Correction**: We must separate `domain.py` (Persistence) from `schemas.py` (Ephemeral Artifacts). Agents yield `Suggestions`, the Orchestrator (or user) decides if they become `Claims`.

### C. Orchestration as a First-Class Citizen
*   **Insight**: Agents do not decide flow. The Orchestrator decides.
*   **Implication**: The logic for "Which agent runs?" and "What context do they get?" belongs in `crew.py` (Orchestrator), not in the agent content.
*   **Correction**: `core.py` becomes a thin runtime layer. It delegates everything to `CrewOrchestrator`.

## 2. Implementation Decisions (Mapping)

Based on these insights, the implementation of Issue #77 is adjusted as follows:

| Architectural Principle | Implementation Action | File Location |
| :--- | :--- | :--- |
| **Contract Separation** | Created `schemas.py` for `AgentOutput` types. Removed from `domain.py`. | `backend/app/agent/schemas.py` |
| **Strict Interaction** | Agents leverage `Task.output_pydantic` to enforce the Contract. No free text. | `backend/app/agent/tasks.py` |
| **Orchestrator Authority** | `CrewOrchestrator` validates outputs and injects `perspective="CAUSA"` metadata. | `backend/app/agent/crew.py` |
| **Runtime Boundary** | `core.py` is stripped of logic, acting only as the API->Orchestrator bridge. | `backend/app/agent/core.py` |

## 3. Risk Mitigation

*   **Risk**: "Chatter" (LLM returning polite conversation instead of data).
    *   **Mitigation**: System prompts in `tasks.py` will explicitly forbid non-JSON output. Orchestrator will discard invalid payloads.
*   **Risk**: Agent "Hallucination" of IDs.
    *   **Mitigation**: Agents return `Suggestions` without IDs (or with temporary ones). The System handles ID assignment upon persistence.

## 4. Conclusion

The "Strict Contract" approach adopted for US #77 is direct execution of the `agent_architecture.md` blueprint. It ensures that adding future agents (e.g., "Devil's Advocate") requires no API changes, only adherence to the `AgentOutput` schema.
