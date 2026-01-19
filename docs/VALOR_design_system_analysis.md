# VALOR Design System Analysis: Ecosystem & Radix UI

## 1. Context & Vision
VALOR is not a single tool but a **multi-agent ecosystem** where human designers collaborate with specialized AI agents (CAUSA, AXIA, THEMIS, etc.). The Design System must support:
*   **Polyphony**: Multiple agents speaking simultaneously (parallelism).
*   **Explicit Normativity**: Visually distinguishing *who* is speaking (Agent Identity) and *why* (Normative Framework).
*   **Human-in-the-loop**: Agents propose (suggestions, alerts), humans decide (mutations).

This analysis maps the architectural needs of VALOR (and specifically CAUSA) to **Radix UI Primitives**, ensuring the frontend is scalable, accessible, and robust.

---

## 2. Core Architectural Needs vs. Radix Primitives

### A. The "Agent Panel" (Multi-Agent Interaction)
*Requirement*: Users need to see output from multiple agents (e.g., Causal Analyst, Devils Advocate). These outputs must be organized, collapsible, and distinct.
*   **Need**: Containerization, Parallel Views, Toggling.
*   **Recommended Primitives**:
    *   **`@radix-ui/react-accordion`**: Perfect for stacking multiple active agents in the `AgentPanelRegion` (Sidebar). Allows expanding/collapsing agent streams.
    *   **`@radix-ui/react-tabs`**: Essential for switching between different *modes* of an agent (e.g., "Suggestions" vs "Log" vs "Settings") or switching perspectives in a unified view.
    *   **`@radix-ui/react-scroll-area`**: Critical for handling long agent outputs (chats, logs) without breaking the layout.

### B. Agent-to-User Feedback (Signals & Suggestions)
*Requirement*: Agents need to nudge the user ("Did you consider this loop?") without blocking workflow.
*   **Need**: Non-blocking notifications, Contextual details, Alerts.
*   **Recommended Primitives**:
    *   **`@radix-ui/react-toast`**: For transient agent signals ("Loop Detected", "Constraint Violated").
    *   **`@radix-ui/react-hover-card`**: **Crucial for Explainability**. When an agent highlights a node, hovering should reveal the *reasoning* (The "Why").
    *   **`@radix-ui/react-alert-dialog`**: For blocking interventions (e.g., THEMIS flagging a legal violation that *cannot* be ignored).

### D. Contextual Operations (Graph Interaction)
*Requirement*: Users interact with nodes/edges to view details, edit properties, or trigger agent actions.
*   **Need**: Menus, Overlays, complexity management.
*   **Recommended Primitives**:
    *   **`@radix-ui/react-context-menu`**: Right-click on Canvas/Node. Essential for invoking specific agents on a specific context ("Ask AXIA about this factor").
    *   **`@radix-ui/react-dialog` (Modal)**: For deep editing (like `EditFactorDetailModal`). We already identified this, but it needs to be the standard "Edit Context".
    *   **`@radix-ui/react-popover`**: For quick, inline edits (e.g., changing connection polarity without opening a full modal).

### E. Structural UI (The Shell)
*Requirement*: Managing the application frame, toolbars, and layout switching.
*   **Need**: Toolbars, Separators, Toggles.
*   **Recommended Primitives**:
    *   **`@radix-ui/react-toolbar`**: Standardizes the top bar (Layout Switcher, Tools).
    *   **`@radix-ui/react-toggle-group`**: Perfect for the "Free / System" layout switch (mutually exclusive options).
    *   **`@radix-ui/react-separator`**: Visual hierarchy in panels and modals.

---

## 3. Specific Perspective Relevancy

### CAUSA (Causal Analyst)
*   **Focus**: Loops, Factors, Uncertainty.
*   **Key UI**:
    *   **ToggleGroup**: Switch Polarities (+ / - / ?).
    *   **Slider**: Confidence levels (0-100%). (*`@radix-ui/react-slider`*)
    *   **HoverCard**: Explain *why* a link is suggested.

### AXIA (Value Analyst)
*   **Focus**: Hierarchies of Public Values, Tensions.
*   **Key UI**:
    *   **Accordion**: Nested value hierarchies.
    *   **Progress**: Value fulfillment scores. (*`@radix-ui/react-progress`*)

### THEMIS (Legal Analyst)
*   **Focus**: Constraints, Rights, Obligations.
*   **Key UI**:
    *   **Alert**: "Breaking Law X".
    *   **Collapsible**: Long legal texts/articles.

---

## 4. Implementation Priority (Recommendation)

### Priority 1: The "Interaction Layer" (CAUSA Support)
These are needed *now* to fix the immediate UX gaps in CAUSA.
1.  **Dialog (Modal)**: For editing factors.
2.  **Select**: For dropdowns (Role, Type).
3.  **ToggleGroup**: For Layout switching and Polarity.
4.  **Slider**: For Confidence (0.0 - 1.0).

### Priority 2: The "Agent Layer" (VALOR Foundation)
These are needed to support the `AgentPanelRegion` and multi-agent future.
1.  **Accordion**: For the Agent Sidebar (stacking agents).
2.  **HoverCard**: For agent annotations/explainability.
3.  **Toast**: For agent notifications.
4.  **Context Menu**: For graph interactions.

## 5. Decision
We will proceed by implementing the **Priority 1** primitives immediately to polish CAUSA, while preparing the "Primitives Library" folder structure to accommodate Priority 2 items as we build the `AgentPanel`.
