# ADR 001: Strict Agent Output Contract via Ephemeral Schemas

## Status
Accepted

## Context
Initial implementation of the Agent system mistakenly mixed domain persistence models (`domain.py`) with agent communication artifacts (`AgentOutput`). This led to tight coupling where agents were functionally modifying database structures, and the orchestrator lacked a clear boundary for validation. 
We need a robust architecture where Agents serve as "Cognitive Modules" that produce strict, validated artifacts, which an Orchestrator then processes.

## Decision
We will enforce a **Strict Output Contract** architecture:

1.  **Ephemeral Schemas (`agent/schemas.py`)**:
    *   All Agent outputs must be defined as Pydantic models in a dedicated `schemas.py` layer.
    *   These are *not* database models. They are transport artifacts (e.g., `Suggestion`, `ConflictSignal`).
    *   They MUST contain metadata: `perspective`, `confidence`, `kind`.

2.  **Orchestrator as Gatekeeper (`agent/crew.py`)**:
    *   The Orchestrator is the *only* component allowed to invoke Agents.
    *   It is responsible for:
        *   Injecting authoritative metadata (e.g., `perspective="CAUSA"`).
        *   Validating LLM output against the Schema.
        *   Filtering low-confidence results.
    *   Agents do not know about the API or the Database; they only know their Input Context and Output Schema.

3.  **Runtime vs Domain Separation**:
    *   `core.py` (Runtime) handles API requests and invokes the Orchestrator.
    *   `domain.py` (Domain) handles Database persistence (`Claim` entities).
    *   The Orchestrator bridges the two: mapping ephemeral `Suggestion` schemas to persistent `Claim` domain objects *if and only if* business logic permits.

4.  **No "Chatter"**:
    *   Agent prompts must strictly forbid free-text output outside the JSON schema.
    *   All "reasoning" must be captured in structured fields (e.g., `reasoning`, `thought_process`).

## Consequences
*   **Positive**:
    *   Frontend is decoupled from Agent internals (renders based on `kind`).
    *   New Agents can be added without Database migrations (as long as they output valid Schemas).
    *   Strict typing allows for easy automated testing of Agent behavior.
*   **Negative**:
    *   Slightly more boilerplate code (mapping Schema -> Domain).
    *   Requires strict prompt discipline.

## Compliance
All future Agent implementations MUST output a `List[AgentOutput]` defined in `schemas.py`. Direct returning of `dict` or `str` is forbidden.
