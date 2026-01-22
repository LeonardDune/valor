# Story #121: Dashboard Environments Widget

## Goal
Implement a "My Environments" widget on the Dashboard that provides a recursive overview of all Organizations, Projects, and Themes the user has access to, including status and proposal counts, replacing manual lists.

## Proposed Changes

### Backend (Python/FastAPI)
#### [NEW] `backend/app/routers/dashboard.py`
- `GET /dashboard/environments`: Recursively queries `(User)-[:MEMBER_OF*]->(Entity)`
- Returns hierarchical JSON:
  ```json
  [
    {
      "type": "ORGANIZATION",
      "id": "...",
      "name": "...",
      "role": "ADMIN",
      "projects": [
        {
          "type": "PROJECT",
          "id": "...",
          "themes": [...]
        }
      ]
    }
  ]
  ```
  ```
#### [MODIFY] `backend/app/main.py`
- Include `dashboard.router`.
#### [MODIFY] `backend/app/routers/proposals.py` & `backend/app/db/crud.py`
- Enhance `Proposal` handling to support `ACCESS_REQUEST` type.
- On `update_status(ACCEPTED)` for `ACCESS_REQUEST`, trigger `add_member` logic.

### Frontend (React)
#### [NEW] `frontend/src/components/dashboard/MyEnvironmentsWidget.tsx`
- Fetches from `/dashboard/environments`.
- Renders recursive tree/list.
- **Actions Menu (`...`) per item**:
    - **Invite Member** (if Admin) -> Opens Invite Modal.
    - **Request Access** (if eligible) -> Creates `ACCESS_REQUEST` Proposal.
    - **View Details** -> Navigates to Workspace.

#### [MODIFY] `frontend/src/views/shell/DashboardLayout.tsx`
- Replace placeholder widgets with `MyEnvironmentsWidget`.

## Verification Plan
### Automated Tests
- `pytest` for the new endpoint (checking recursion and permissions).
### Manual Verification
- Login as user.
- Verify Dashboard shows tree structure.
- Verify verifying navigation works (clicking Theme opens Workspace).
