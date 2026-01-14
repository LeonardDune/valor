import json
import subprocess
import re

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def main():
    print("Fetching issues...")
    # Fetch all open issues
    issues_json = run_command("gh issue list --state open --limit 100 --json number,title,labels")
    issues = json.loads(issues_json)
    
    pattern = re.compile(r"\[US-\d+\]\s*(.*)")
    
    for issue in issues:
        title = issue['title']
        number = issue['number']
        
        match = pattern.match(title)
        if match:
            new_title = match.group(1)
            print(f"Renaming #{number}: '{title}' -> '{new_title}'")
            # Execute rename
            # escape double quotes just in case
            safe_title = new_title.replace('"', '\\"')
            run_command(f'gh issue edit {number} --title "{safe_title}"')
        else:
            print(f"Skipping #{number}: '{title}' (No [US-XX] prefix)")

if __name__ == "__main__":
    main()
