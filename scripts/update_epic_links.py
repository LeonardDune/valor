import subprocess
import json

EPIC_ID = "109"
STORIES = [
    {"title": "[Backend] Datamodel migratie naar Proposal-lifecycle", "id": "110", "url": "https://github.com/LeonardDune/valor/issues/110"},
    {"title": "[Backend] Proposal Management API", "id": "111", "url": "https://github.com/LeonardDune/valor/issues/111"},
    {"title": "[Frontend] Dashboard Shell & Draft State", "id": "112", "url": "https://github.com/LeonardDune/valor/issues/112"},
    {"title": "[Frontend] Cross-perspective Activity Feed", "id": "113", "url": "https://github.com/LeonardDune/valor/issues/113"},
    {"title": "[Fullstack] Conflict Detectie & Visualisatie", "id": "114", "url": "https://github.com/LeonardDune/valor/issues/114"},
    {"title": "[Agent] Agent Output structureren als Proposals", "id": "115", "url": "https://github.com/LeonardDune/valor/issues/115"},
    {"title": "[Arch] Perspective & View Isolation Modules", "id": "116", "url": "https://github.com/LeonardDune/valor/issues/116"}
]

def run_gh_command(args):
    result = subprocess.run(['gh'] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running gh {' '.join(args)}: {result.stderr}")
        return None
    return result.stdout.strip()

def main():
    print(f"Updating Epic #{EPIC_ID} with linked stories...")
    
    # 1. Get current body
    current_body = run_gh_command(['issue', 'view', EPIC_ID, '--json', 'body', '-q', '.body'])
    if not current_body:
        print("Could not fetch current body.")
        return

    # 2. Build new section
    new_section = "\n\n## Linked User Stories\n"
    for story in STORIES:
        new_section += f"- [{story['title']} #{story['id']}]({story['url']})\n"

    # 3. Update issue
    # We combine them. Note: we don't want to duplicate if run twice.
    if "## Linked User Stories" in current_body:
        print("Epic already has linked stories section. Aborting to avoid duplication.")
        return

    new_body = current_body + new_section
    
    result = run_gh_command(['issue', 'edit', EPIC_ID, '--body', new_body])
    if result is not None:
        print(f"Successfully updated Epic #{EPIC_ID}.")
        print(result)

if __name__ == "__main__":
    main()
