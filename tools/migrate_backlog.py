import re
import subprocess
import time
import sys
import os

BACKLOG_PATH = "docs/backlog.md"

def run_command(cmd):
    """Runs a shell command and returns stdout."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}\n{e.stderr}")
        return None

def ensure_label(name, color="ededed"):
    """Creates a label if it doesn't exist."""
    print(f"Ensuring label: {name}")
    run_command(f"gh label create \"{name}\" --color {color} --force")

def get_existing_issues():
    """Returns a set of existing issue titles (or just US-IDs) to avoid duplicates."""
    print("Fetching existing issues...")
    output = run_command("gh issue list --state all --limit 500 --json title")
    if not output:
        return set()
    import json
    try:
        issues = json.loads(output)
        return {issue['title'] for issue in issues}
    except:
        return set()

def parse_backlog():
    """Parses the backlog.md file."""
    with open(BACKLOG_PATH, 'r') as f:
        lines = f.readlines()

    current_epic = None
    issues = []
    current_issue = None

    for line in lines:
        line = line.strip()
        
        # Epic Detection
        epic_match = re.match(r"^### Epic (\d+): (.+)", line)
        if epic_match:
            epic_num = epic_match.group(1)
            epic_raw_name = epic_match.group(2)
            # Create a simplified label name "epic:conversational-reasoning"
            # Limit to 3 words
            slug = "-".join(epic_raw_name.split()[:3]).lower()
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            
            label_name = f"epic:{slug}"
            current_epic = label_name # Use the label name as the identifier for issues
            
            # Ensure label exists
            ensure_label(label_name, "0e8a16")
            continue

        # User Story Detection
        us_match = re.search(r"\*\s+\*\*\[(US-\d+)\]\s+(.+?)\*\*: (.+)", line)
        if us_match:
            # Save previous issue
            if current_issue:
                issues.append(current_issue)
            
            us_id = us_match.group(1)
            title = us_match.group(2)
            desc = us_match.group(3)
            
            current_issue = {
                "title": f"[{us_id}] {title}",
                "body": f"**User Story**\n{desc}\n\n**Epic Reference**: {current_epic}\n",
                "labels": [],
                "status": "Backlog"
            }
            if current_epic:
                current_issue["labels"].append(current_epic)

            continue

        # Attributes
        if current_issue:
            prio_match = re.match(r"\* \*\*Prioriteit\*\*: (.+)", line)
            if prio_match:
                prio = prio_match.group(1).lower()
                if "hoog" in prio: current_issue["labels"].append("priority:high")
                elif "medium" in prio: current_issue["labels"].append("priority:medium")
                elif "laag" in prio: current_issue["labels"].append("priority:low")
            
            status_match = re.match(r"\* \*\*Status\*\*: (.+)", line)
            if status_match:
                status = status_match.group(1).lower()
                current_issue["status"] = status
            
            notes_match = re.match(r"\* \*\*Notities\*\*: (.+)", line)
            if notes_match:
                current_issue["body"] += f"\n**Notes**\n{notes_match.group(1)}\n"

    if current_issue:
        issues.append(current_issue)
    
    return issues

def main():
    if not os.path.exists(BACKLOG_PATH):
        print(f"Backlog file not found at {BACKLOG_PATH}")
        return

    existing_titles = get_existing_issues()
    issues = parse_backlog()

    print(f"Found {len(issues)} user stories to migrate.")
    
    for issue in issues:
        if issue['title'] in existing_titles:
            print(f"Skipping existing issue: {issue['title']}")
            continue

        print(f"Creating: {issue['title']}")
        
        # Construct GH command
        labels_arg = " ".join([f'--label "{l}"' for l in issue['labels']])
        
        # Escape body for shell (simple version, ideally use gh stdin)
        # We will use subprocess input to avoid shell escaping hell
        
        cmd = ["gh", "issue", "create", "--title", issue['title'], "--body", issue['body']]
        for l in issue['labels']:
            cmd.extend(["--label", l])
            
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Created: {result.stdout.strip()}")
            
            # Handle Status (Close if Done)
            if "gereed" in issue['status'] or "done" in issue['status']:
                issue_url = result.stdout.strip()
                subprocess.run(["gh", "issue", "close", issue_url], check=True)
                print(f"Closed: {issue_url}")
                
            time.sleep(1) # Rate limit protection
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to create issue {issue['title']}: {e.stderr}")

if __name__ == "__main__":
    main()
