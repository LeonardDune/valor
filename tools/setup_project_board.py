import subprocess
import json
import time

OWNER = "LeonardDune" 
PROJECT_TITLE = "Valor Roadmap"

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def get_projects():
    output = run_command(f"gh project list --owner {OWNER} --format json")
    if output:
        return json.loads(output)
    return []

def create_project():
    print(f"Creating project '{PROJECT_TITLE}'...")
    # New Projects (Beta/Memex)
    output = run_command(f"gh project create --owner {OWNER} --title \"{PROJECT_TITLE}\" --format json")
    if output:
        return json.loads(output)
    return None

def get_issues():
    output = run_command("gh issue list --state all --limit 100 --json id,number,title")
    if output:
        return json.loads(output)
    return []

def add_item_to_project(project_id, content_id):
    # gh project item-add <number> --owner <owner> --url <issue-url>
    # Actually checking syntax...
    # format: gh project item-add <project-number> --owner <owner> --url <url>
    pass 

def main():
    # 1. Find or Create Project
    projects = get_projects()
    project = next((p for p in projects['projects'] if p['title'] == PROJECT_TITLE), None) if projects else None
    
    if not project:
        project = create_project()
        if not project:
            print("Failed to create project.")
            return
        # project object from create might differ structure
        # gh project create returns: { "url": "...", "number": 1, "id": "PVT_..." }
        project_number = project['number']
    else:
        project_number = project['number']
        
    print(f"Using Project #{project_number} ({PROJECT_TITLE})")

    # 2. Get Issues
    issues = get_issues()
    print(f"Found {len(issues)} issues to add...")

    # 3. Add to Project
    # We need the Issue Global Node ID or URL? 
    # gh project item-add usage: gh project item-add <number> --owner <owner> --url <issue-url>
    
    # Let's get full URLs
    issues_full = json.loads(run_command("gh issue list --state all --limit 100 --json url,title"))
    
    for issue in issues_full:
        print(f"Adding {issue['title']}...")
        run_command(f"gh project item-add {project_number} --owner {OWNER} --url {issue['url']}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
