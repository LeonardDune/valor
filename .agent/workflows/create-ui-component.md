---
description: Standards-compliant workflow for creating or refactoring UI components. Enforces Design System primitives and Dutch localization.
---

# UI Component Creation Workflow

Use this workflow whenever you are asked to create a new UI component or significantly refactor an existing one.

## 1. Pre-Flight Check (Global Rules)
- [ ] **Read the Rules**: View `.agent/skills/agent-memory/memories/best-practices/design-system-and-api-integrity.md`.
- [ ] **Language**: Confirm all end-user text will be in **Dutch (NL)**.
- [ ] **Formatting**: Confirm date/number formatting is set to `nl-NL`.

## 2. Component Primitives Audit
Before writing `<div>` wrappers, check for existing Shadcn/Radix components in `src/components/ui/`.
- [ ] Run `ls src/components/ui/` to see available primitives.
- [ ] **Mandatory Usage**:
    - Use `<Card>`, `<CardHeader>`, `<CardContent>` for containers.
    - Use `<Button>` for actions.
    - Use `<Input>`, `<Select>`, `<Textarea>` for forms.
    - Use `<ScrollArea>` for scrollable lists.
- [ ] **Missing Primitive?**: If a primitive is needed but missing (e.g. `DropdownMenu`), **INSTALL IT** via `npm install` and add the component file. Do not hack a workaround.

## 3. Implementation Steps
1.  **Scaffold**: Create the file structure.
2.  **Imports**: Import necessary primitives from `@/components/ui/...`.
3.  **Strings**: Write all static strings in Dutch immediately.
4.  **Styling**: Use utility classes (`cn(...)`) only for layout gaps/padding. Let the primitives handle colors/rounding/shadows.

## 4. Post-Implementation Verification
- [ ] **Lint Check**: Ensure no unused imports or strict type errors.
- [ ] **Localization Check**: Scan the code for English strings (e.g., "Loading...", "Submit", "Error"). Replace with Dutch if found.
