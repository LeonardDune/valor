# 🏗️ Project Specific Coding Standards (Valor Stack)

## 1. Stack Implementation & Security
* **Frontend Configuration:** Use `import.meta.env.VITE_*` (Vite standards) for environment variables.
* **Backend Configuration:** Use `config.py` (Pydantic Settings) or strictly `os.getenv`.
* **Type Safety:**
    * **Frontend:** Strict TypeScript. Define interfaces for all props and API responses. Avoid `any`.
    * **Backend:** Python Type Hints on all function signatures.

## 2. React & UI Architecture
* **Component Structure:** Functional Components only. One component per file. PascalCase filenames.
* **Import Strategy:** Use path aliases: `import { Button } from "@/components/ui/button"`.

### UI Primitives (Shadcn & Radix)
* **Primary Library:** Use **Shadcn/UI** for all standard components (Buttons, Inputs, Cards).
    * *Style:* "New York"
    * *Color:* Zinc
    * *Icons:* Lucide React
* **Radix UI Mandate:** For complex interactive primitives NOT covered by Shadcn, you **MUST** use **Radix UI Primitives** (`@radix-ui/react-*`).
    * **Goal:** Accessibility (A11y) & Keyboard Navigation.
    * **Rule:** Do not build Modals, Popovers, or Tabs from scratch using `divs`. Use the Radix primitive and style it with Tailwind.
* **Styling Strategy:**
    * **Tailwind:** Use utility classes.
    * **Semantic Tokens:** NEVER use arbitrary hex/rgb values. Use `bg-destructive`, `text-muted-foreground`, `border-input` (mapped in `src/index.css`).
    * **Z-Index:** Strictly follow the global scale (`--z-canvas` -> `--z-modal`).
* **No Substitutions**: If a Shadcn/Radix component (like `DropdownMenu`) is missing from `components/ui`, **INSTALL IT**.
    *   Check `components.json` and `package.json`.
    *   Install primitive: `npm install @radix-ui/react-dropdown-menu`.
    *   Create component: `components/ui/dropdown-menu.tsx` (following Shadcn pattern).
    *   **NEVER** use a "similar" component (e.g., `Popover`) as a patchy workaround.

## 3. Directory Structure
* **UI Components:** `src/components/ui/` (Shadcn/Radix only).
* **Feature Components:** `src/components/<feature-name>/`.
* **Global CSS:** `src/index.css` contains the design tokens.


## 4. API Architecture
*   **Centralized Service**: All backend communication MUST go through `src/services/api.ts`.
    *   **Prohibited**: `fetch('/api/...')` inside React components.
    *   **Required**: `await api.getDashboardEnvironments()` or `await api.createProposal(...)`.
    *   *Rationale*: Centralized error handling, type safety, and automatic Auth header injection.

## 5. Localization
*   **Dutch Only**: All user-facing text, labels, and buttons MUST be in **Dutch**.
    *   *Wrong*: "Open Workspace", "Invite Member".
    *   *Right*: "Werkruimte Openen", "Lid Uitnodigen".

## 6. Identity & Context
*   **Real IDs**: Never use placeholders like `'placeholder-user-id'`.
    *   Use `useAuth()` hook to retrieve the current session/user.
    *   If ID is missing, handle the error/loading state explicitly.