# Valor Coding Standards

## Network & API
*   **NO HARDCODED CONFIGURATION:** Never hardcode sensitive or environment-dependent values (URLs, API keys, passwords, secrets, ports, etc.).
    *   **Frontend:** Use `import.meta.env.VITE_*`.
    *   **Backend:** Use `config.py` ( Pydantic settings) or `os.getenv`.
*   **Centralized Configuration:** All configuration must be centralized. Do not scatter `os.getenv` calls throughout the business logic.

## React & Components
*   **Functional Components:** Use functional components with hooks.
*   **TypeScript:** Use strict typing. Avoid `any`. Define interfaces for all props and data models.

## Workflow Rules
*   **STRICT VALIDATION GATES:** You are absolutely FORBIDDEN from proceeding to a new User Story (US) or major task without explicit user confirmation of the previous one.
*   **PAUSE FOR FEEDBACK:** After completing a Functional Requirement, stop and ask the user to verify. Do not assume success.
*   **NO CHAINING:** Do not implement US-X and US-Y in the same turn or session without intermediate approval.

## Architectural Integrity
*   **READ BEFORE ACTING:** Before modifying core logic (Shell, Runners, Session), you MUST read the referenced architectural documentation (e.g. `docs/rearchitecture_layouts.md`).
*   **ISOLATION FIRST:** When the architecture specifies isolation (e.g., Layouts, Perspectieven), do NOT optimize for code reuse if it compromises that isolation. Explicit duplication is better than implicit coupling.
*   **STATELESSNESS:** Core logical units (Runners, Agents) should be stateless where possible. State belongs in the Shell or Store, strictly scoped.

## Design System & UI
*   **Foundation:** Use **Shadcn/UI** as the base component library.
    *   **Style:** "New York"
    *   **Base Color:** Zinc
    *   **Radius:** 0.5rem
    *   **Icons:** Lucide React
*   **Component Location:** All Shadcn primitives must reside in `src/components/ui`.
*   **Styling Strategy:**
    *   **Global Tokens:** Use CSS variables defined in `src/index.css` for all colors and layout constants.
    *   **Tailwind:** Use the extended Tailwind configuration which maps to these variables (e.g., `bg-canvas`, `text-causal-positive`).
    *   **No Hardcoded Colors:** Do not use arbitrary hex or rgb values in components. Always utilize the semantic tokens.
*   **Path Aliases:** Use `@/` to import from `src/` (e.g., `import { Button } from "@/components/ui/button"`).
*   **Z-Index:** Respect the global z-index scale defined in `index.css` (`--z-canvas`, `--z-panel`, `--z-overlay`, `--z-modal`, `--z-cursor`).
