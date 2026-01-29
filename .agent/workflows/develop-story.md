---
name: develop-story
description: End-to-end development workflow: Branching, MCP-based Issue tracking, Project updates, and PR management.
trigger: /develop-story
version: 3.2
scope: global
parameters:
  github_repository:
    description: Target GitHub repository (owner/repo)
    required: true
  github_project_id:
    description: GitHub Project board ID (Number)
    required: true
  github_project_owner:
    description: Owner of the GitHub project (User or Org)
    required: true
  issue_number:
    description: GitHub Issue number of the User Story
    required: true
  feature_branch_prefix:
    description: Prefix for feature branches
    default: feature
  epic_branch_prefix:
    description: Prefix for epic branches
    default: epic
  labels_in_progress:
    description: Label to mark issues as in-progress
    default: in-progress
  labels_done:
    description: Label to mark issues as done
    default: done
  project_status_field:
    description: The name of the status field in the Project Board
    default: Status
  project_status_todo:
    description: Value for Todo
    default: Todo
  project_status_in_progress:
    description: Value for In Progress
    default: In Progress
  project_status_done:
    description: Value for Done
    default: Done
---

# Workflow: Develop Story

## 0. Rules of Engagement
**CRITICAL SAFETY RULES:**
1.  **No Direct Commits:** Never commit directly to `main`. Always use a feature or epic branch.
2.  **No Auto-Merge:** You are FORBIDDEN from merging a PR without explicit user confirmation in the chat.
3.  **Project Sync:** Keep the GitHub Project Board in sync with the actual state.
4.  **Database Safety:** 
    *   **Dev:** Verify schema changes on Dev DB using verification scripts.
    *   **Prod:** Schema changes MUST be applied to Production Database BEFORE merging matching code to `main`.

---

## 1. Initialization & Project Sync
> **Agent Instruction:**
> Start the development process by setting up the environment and notifying the team via status updates.

### 1.1 Create Branch (Smart Detection)
Determine if this is an Epic or a Story and create the appropriate branch.
```bash
# Get issue details
JSON=$(gh issue view {issue_number} --json title,labels)
TITLE=$(echo $JSON | jq -r .title | sed 's/[^a-zA-Z0-9]/ /g' | awk '{$1=$1};1' | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | cut -c1-30)
LABELS=$(echo $JSON | jq -r .labels[].name)

# Determine Branch Type and Base
if [[ "$LABELS" == *"epic"* ]] || [[ "$TITLE" == "epic"* ]]; then
  PREFIX="{epic_branch_prefix}"
  echo "Detected EPIC. Creating integration branch from main."
  BASE_BRANCH="main"
else
  PREFIX="{feature_branch_prefix}"
  echo "Detected STORY. Creating feature branch."
  # Ask user for base branch preference if working inside an Epic context
  read -p "Is this story part of an active Epic branch? (Enter branch name or press Enter for 'main'): " USER_BASE
  BASE_BRANCH=${USER_BASE:-main}
fi

BRANCH_NAME="$PREFIX/issue-{issue_number}-$TITLE"

# Execute
git checkout $BASE_BRANCH
git pull
git checkout -b "$BRANCH_NAME"
echo "Switched to branch: $BRANCH_NAME (based on $BASE_BRANCH)"
```

### 1.2 Update Issue Labels (MCP)
Mark the issue as active using the MCP Tool.
**Tool:** `github-mcp-server_issue_write` (method='update')
**Args:** `add_labels=['{labels_in_progress}']`

### 1.3 Update Project Status: In Progress (CLI)
Move the card on the project board.
```bash
# 1. Get Global Project ID
PROJECT_GLOBAL_ID=$(gh project list --owner {github_project_owner} --format json --jq '.projects[] | select(.number == {github_project_id}) | .id')

# 2. Add Item if not exists
gh project item-add "$PROJECT_GLOBAL_ID" --owner {github_project_owner} --url "https://github.com/{github_repository}/issues/{issue_number}" > /dev/null 2>&1

# 3. Get Item ID
ITEM_ID=$(gh project item-list "$PROJECT_GLOBAL_ID" --owner {github_project_owner} --format json --jq '.items[] | select(.content.number == {issue_number}) | .id')

# 4. Get Field and Option IDs
FIELD_DATA=$(gh project field-list "$PROJECT_GLOBAL_ID" --owner {github_project_owner} --format json)
STATUS_FIELD_ID=$(echo "$FIELD_DATA" | jq -r '.fields[] | select(.name == "{project_status_field}") | .id')
OPTION_ID=$(echo "$FIELD_DATA" | jq -r ".fields[] | select(.name == \"{project_status_field}\") | .options[] | select(.name == \"{project_status_in_progress}\") | .id")

# 5. Update Status
if [ -n "$ITEM_ID" ] && [ -n "$STATUS_FIELD_ID" ] && [ -n "$OPTION_ID" ]; then
  gh project item-edit --id "$ITEM_ID" --field-id "$STATUS_FIELD_ID" --project-id "$PROJECT_GLOBAL_ID" --single-select-option-id "$OPTION_ID"
  echo "Project status updated to: {project_status_in_progress}"
else
  echo "Error: Could not update project status. Missing ID(s)."
fi
```

### 1.4 Context Setup
Create/Update a local `implementation_plan.md`.

*   **Load Global Standards:** Read `~/.gemini/antigravity/resources/global-coding-standards.md`.
*   **Load Project Standards:** Read `.agent/resources/project-coding-standards.md`.

Add to your current `task.md` or context file.

---

## 2. Development Phase (Loop)
> **Agent Instruction:** This is the interactive coding phase.

1.  Present the plan from `implementation_plan.md` to the user.
2.  Write code and tests.
3.  Stop and ask for user verification/acceptance before proceeding.

---

### 2.5 Database Verification (If Schema Changed)
**CRITICAL:** If your changes involve `schema.cypher` or data migrations:

1.  **Run Verification:** You MUST run a verification script (like `verify_space_model.py`) against the **Development Database**.
2.  **Confirm Success:** Ensure the script passes without errors.
3.  **Document:** Include the verification output or confirmation in the PR description.

---

## 3. Pull Request Creation
> **Agent Instruction:** Once the user is satisfied with the code, create the PR.

### 3.1 Create PR (MCP)
**Tool:** `github-mcp-server_pull_request_create`
**Args:**
*   `head`: (Current Branch Name)
*   `base`: (The base branch selected in Step 1.1)
*   `title`: "feat: (Get title from Issue #{issue_number})"
*   `body`: "Fixes #{issue_number}\n\nImplemented via Antigravity workflow."

### 3.2 Pause for Approval
**CRITICAL STOP:** Report the PR URL to the user. DO NOT PROCEED until the user explicitly types: "Merge PR" or "Approved". If the user wants changes, go back to Step 2.

---

## 4. Finalization (Only after User Approval)
### 4.1 Merge PR (CLI)
Merge the PR and delete the remote branch.
```bash
gh pr merge --merge --delete-branch
```

### 4.2 Local Cleanup
```bash
# Return to the base branch used in Step 1
git checkout (The base branch used in Step 1.1)
git pull
git branch -d (Previous Branch Name)
```

### 4.3 Update Issue Labels (MCP)
Swap the "In Progress" label for "Done".
**Tool:** `github-mcp-server_issue_write` (method='update')
**Args:** `remove_labels=['{labels_in_progress}']`, `add_labels=['{labels_done}']`

### 4.4 Update Project Status: Done (CLI)
Finalize the project board status.
```bash
# Re-run logic to get ITEM_ID, STATUS_FIELD_ID, OPTION_ID for "Done" status
# [Insert same script block as 1.3 but with project_status_done]
```

---

## 5. Strategy for Epics
> **Agent Instruction:** Consult this strategy when the issue is an Epic or part of an Epic.

**Context:** Epics represent larger bodies of work. They require a dedicated integration branch.

**The Flow:**
1.  **Integration Branch:** `epic/<issue-id>-<description>` (Branches off `main`).
2.  **Feature Branches:** Stories branch off the Epic branch.
3.  **Final Merge:** Epic -> Main.

### 5.1 CRITICAL: Production Migration Gate (Final Merge)
**BEFORE merging an Epic Branch into `main`**:

1.  **SAFETY CHECK:** Confirm with user: "Have schema changes been applied to PRODUCTION DB?"
2.  **MANUAL ACTION:** User/Agent must run schema migration scripts against Production.
3.  **VERIFICATION:** Only proceed if Production DB is confirmed valid.
4.  **MERGE:** Use `gh pr merge --merge` to merge the Epic Branch into `main`.
