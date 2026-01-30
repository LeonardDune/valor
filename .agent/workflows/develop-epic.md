---
name: develop-epic
description: Initialize a new Epic: Create integration branch and set status.
trigger: /develop-epic
version: 1.0
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
    description: GitHub Issue number of the Epic
    required: true
  epic_branch_prefix:
    description: Prefix for epic branches
    default: epic
  labels_in_progress:
    description: Label to mark issues as in-progress
    default: in-progress
  project_status_field:
    description: The name of the status field in the Project Board
    default: Status
  project_status_in_progress:
    description: Value for In Progress
    default: In Progress
---

# Workflow: Develop Epic

## 1. Initialization
> **Agent Instruction:**
> Initialize the Epic structure.

### 1.1 Create Epic Branch
```bash
# Get issue details
JSON=$(gh issue view {issue_number} --json title)
TITLE=$(echo $JSON | jq -r .title | sed 's/Epic - //I' | sed 's/[^a-zA-Z0-9]/ /g' | awk '{$1=$1};1' | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | cut -c1-40)

BRANCH_NAME="{epic_branch_prefix}/issue-{issue_number}-$TITLE"

# Execute
git checkout main
git pull
git checkout -b "$BRANCH_NAME"
echo "Switched to Epic branch: $BRANCH_NAME"
```

### 1.2 Update Issue Labels
**Tool:** `github-mcp-server_issue_write` (method='update')
**Args:** `add_labels=['{labels_in_progress}']`

### 1.3 Update Project Status
Move the card on the project board to "In Progress".
(Use standard `gh project item-edit` logic as in develop-story).

## 2. Strategy Record
> **Agent Instruction:**
> Note the Epic Branch name in `task.md` or a dedicated context file so you remember it for child stories.
