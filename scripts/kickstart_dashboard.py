import subprocess
import json
import os

# Configuration
REPO = "LeonardDune/valor"
PROJECT_ID = 2
PROJECT_OWNER = "LeonardDune"
EPIC_TEMPLATE_PATH = "/home/renzo/.gemini/antigravity/resources/templates/epic.md"
STORY_TEMPLATE_PATH = "/home/renzo/.gemini/antigravity/resources/templates/user-story.md"

# Specific Data
EPIC_DATA = {
    "title": "Collaboratieve Architectuur & Dashboard",
    "goal": "Implementatie van de algemene collaboratie-architectuur en het gebruikersdashboard, waarin status, voorstellen en conflicten centraal staan.",
    "design_intent": "Het dashboard is GEEN takenlijst, maar een 'situational awareness' interface. Collaboratie gebeurt via expliciete 'Proposals' en 'Statussen' in plaats van directe mutaties door eender wieden.",
    "value": "Maakt asynchroon samenwerken mogelijk zonder starre rollen en maakt conflicten inzichtelijk als waardevolle data.",
    "in_scope": "- Backend Datamodel migratie (Proposal/Status)\n- Proposal API\n- Dashboard Shell & State\n- Activity Feed\n- Conflict Visualisatie\n- Agent Structured Outputs",
    "out_of_scope": "- Domeinspecifieke logica in de views (wordt generiek opgezet)\n- Geavanceerde graph algoritmes voor conflictresolutie (start simpel)",
    "assumptions": "- Bestaande data kan worden gemigreerd naar status='accepted'\n- Neo4j performance blijft acceptabel bij queries over de hele graph"
}

STORIES = [
    {
        "title": "[Backend] Datamodel migratie naar Proposal-lifecycle",
        "actor": "Developer",
        "need": "dat het datamodel 'Proposal', 'Conflict' en 'Status' ondersteunt en bestaande data gemigreerd is",
        "value": "we de applicatie niet 'breken' voor bestaande data en de basis leggen voor voorstellen",
        "context": "Huidige data heeft geen expliciete status. Alles wordt gezien als 'waarheid'. Dit moet veranderen.",
        "acceptance_criteria": "- Node model heeft `status` veld (enum)\n- Proposal model bestaat\n- Conflict model bestaat\n- Migratiescript gedraaid: alle bestaande nodes = accepted",
        "labels": ["backend", "migration", "critical"]
    },
    {
        "title": "[Backend] Proposal Management API",
        "actor": "Developer",
        "need": "API endpoints om wijzigingen als voorstel in te dienen",
        "value": "frontend en agents a-synchroon wijzigingen kunnen voorstellen",
        "context": "CRUD is nu direct. Moet via /proposals/ endpoints lopen.",
        "acceptance_criteria": "- POST /proposals/\n- PUT /proposals/{id}/accept\n- PUT /proposals/{id}/reject\n- GET /proposals (filter op status)",
        "labels": ["backend", "api"]
    },
    {
        "title": "[Frontend] Dashboard Shell & Draft State",
        "actor": "Gebruiker",
        "need": "visueel onderscheid tussen 'live' data en 'draft' data",
        "value": "ik niet verward raak over wat echt is en wat een voorstel is",
        "context": "Nieuwe layout nodig.",
        "acceptance_criteria": "- DashboardLayout component\n- Store update voor Draft Mode\n- Visuele indicatoren (badges/borders) voor draft items",
        "labels": ["frontend", "ux"]
    },
    {
        "title": "[Frontend] Cross-perspective Activity Feed",
        "actor": "Gebruiker",
        "need": "een overzicht van recente voorstellen en wijzigingen",
        "value": "ik weet waar de discussie plaatsvindt",
        "context": "Aggregatie over projecten heen.",
        "acceptance_criteria": "- ActivityFeed component\n- Toont: Nieuwe voorstellen, statuswijzigingen, nieuwe conflicten\n- Sorteerbaar op datum",
        "labels": ["frontend", "visualization"]
    },
    {
        "title": "[Fullstack] Conflict Detectie & Visualisatie",
        "actor": "Gebruiker",
        "need": "zichtbaarheid van strijdige claims of definities",
        "value": "ik inhoudelijke spanning kan onderzoeken",
        "context": "Conflict is een first-class citizen.",
        "acceptance_criteria": "- Backend: logic to detect simple conflicts\n- Frontend: ConflictPanel component\n- Weergave van de tegenstrijdige nodes/claims",
        "labels": ["fullstack", "conflict-resolution"]
    },
    {
        "title": "[Agent] Agent Output structureren als Proposals",
        "actor": "AI Agent",
        "need": "mijn suggesties als formele Proposals indienen",
        "value": "mijn werk controleerbaar en integreerbaar is",
        "context": "Nu doet de agent vaak directe aanpassingen of geeft platte tekst.",
        "acceptance_criteria": "- Agent Output Parser update\n- CrewAI tasks geconfigureerd op JSON output matching Proposal schema",
        "labels": ["agent", "ai"]
    },
    {
        "title": "[Arch] Perspective & View Isolation Modules",
        "actor": "Architect",
        "need": "nieuwe perspectieven modulair toe te voegen",
        "value": "de codebase onderhoudbaar blijft bij uitbreiding",
        "context": "Herstructurering nodig om spaghetti te voorkomen.",
        "acceptance_criteria": "- PerspectiveShell component\n- Plugin-achtige structuur voor Views\n- Geen hard dependencies tussen views",
        "labels": ["architecture", "refactor"]
    }
]

def read_template(path):
    with open(path, 'r') as f:
        return f.read()

def fill_template(template, data):
    content = template
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        # Fallback for missing keys in template to empty string or keep generic ?
        # The templates use specific keys.
        content = content.replace(placeholder, str(value))
    
    # Clean up any leftover basic placeholders if necessary, or just leave them.
    # We'll assume the dict covers the main ones.
    # user-story.md adds defaults for sections not in dict?
    if "{{design_intent}}" in content and "design_intent" not in data:
        content = content.replace("{{design_intent}}", "Zie Epic.")
    if "{{status}}" in content:
        content = content.replace("{{status}}", "Ready")
    return content

def run_gh_command(args):
    result = subprocess.run(['gh'] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running gh {' '.join(args)}: {result.stderr}")
        return None
    return result.stdout.strip()

def create_issue(title, body, labels):
    # labels to comma string
    label_str = ",".join(labels)
    output = run_gh_command([
        'issue', 'create',
        '--repo', REPO,
        '--title', title,
        '--body', body,
        '--label', label_str
    ])
    if output:
        # Output is the URL, e.g. https://github.com/LeonardDune/valor/issues/123
        # We need the number and the URL
        return output
    return None

def add_to_project(issue_url):
    # gh project item-add 2 --owner LeonardDune --url <URL>
    run_gh_command([
        'project', 'item-add', str(PROJECT_ID),
        '--owner', PROJECT_OWNER,
        '--url', issue_url
    ])

def ensure_label(name, color="ededed"):
    # Try to create label, ignore if it exists (returns non-zero)
    subprocess.run(['gh', 'label', 'create', name, '--color', color, '--force'], capture_output=True)

def main():
    print("--- Starting Feature Kickstart Automation ---")
    
    # 0. Ensure Labels
    print("Ensuring labels exist...")
    needed_labels = {
        "status:idea-capture": "c2e0c6",
        "status:ready": "0e8a16",
        "epic": "b60205",
        "user-story": "63a4d6",
        "backend": "d4c5f9",
        "frontend": "c2e0c6",
        "fullstack": "006b75",
        "agent": "d4c5f9", 
        "ai": "d4c5f9",
        "architecture": "0052cc",
        "refactor": "e99695",
        "migration": "d93f0b",
        "critical": "b60205",
        "api": "c5def5",
        "ux": "c5def5",
        "visualization": "1d76db",
        "conflict-resolution": "f9d0c4"
    }
    for name, color in needed_labels.items():
        ensure_label(name, color)

    # 1. Create Epic
    print("Creating Epic...")
    epic_template = read_template(EPIC_TEMPLATE_PATH)
    epic_body = fill_template(epic_template, EPIC_DATA)
    
    epic_url = create_issue(f"EPIC: {EPIC_DATA['title']}", epic_body, ["epic", "status:idea-capture"])
    
    if not epic_url:
        print("Failed to create Epic. Aborting.")
        return

    print(f"Epic Created: {epic_url}")
    epic_number = epic_url.split('/')[-1]
    
    print("Adding Epic to Project...")
    add_to_project(epic_url)
    
    # 2. Create Stories
    print(f"Creating {len(STORIES)} User Stories...")
    story_template = read_template(STORY_TEMPLATE_PATH)
    
    created_stories = []
    
    for story in STORIES:
        print(f"  > Creating: {story['title']}")
        story_body = fill_template(story_template, story)
        # Append Link to Epic
        story_body += f"\n\nPart of Epic #{epic_number}"
        
        # Combine labels
        labels = ["user-story", "status:ready"] + story.get("labels", [])
        
        story_url = create_issue(story['title'], story_body, labels)
        
        if story_url:
            add_to_project(story_url)
            created_stories.append({"title": story['title'], "url": story_url})
        else:
            print(f"    Failed to create story: {story['title']}")

    # Summary
    print("\n--- Kickstart Summary ---")
    print(f"Epic: {EPIC_DATA['title']} - {epic_url}")
    print("Stories:")
    for s in created_stories:
        print(f"- {s['title']}: {s['url']}")

if __name__ == "__main__":
    main()
