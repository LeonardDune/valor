import subprocess
import json

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()

def main():
    owner = "LeonardDune"
    project_number = 2
    issue_number = 152
    status_field_name = "Status"
    status_value = "In Progress"
    project_id = "PVT_kwHOADofz84BMi8i"  # Hardcoded from previous lookup

    # 1. Get Fields
    print("Fetching Fields...")
    fields_json = run_command(f"gh project field-list {project_number} --owner {owner} --format json")
    if not fields_json: return
    fields_data = json.loads(fields_json)
    
    # 'fields' key is likely top level
    fields = fields_data.get('fields', [])
    status_field = next((f for f in fields if f['name'] == status_field_name), None)
    
    if not status_field:
        print("Status field not found.")
        print(f"Available fields: {[f['name'] for f in fields]}")
        return
    status_field_id = status_field['id']
    
    option = next((o for o in status_field['options'] if o['name'] == status_value), None)
    if not option:
        print(f"Option '{status_value}' not found.")
        print(f"Available options: {[o['name'] for o in status_field['options']]}")
        return
    option_id = option['id']

    # 2. Get Item ID
    print("Fetching Item ID...")
    items_json = run_command(f"gh project item-list {project_number} --owner {owner} --format json")
    if not items_json: return
    items_data = json.loads(items_json)
    
    item = next((i for i in items_data['items'] if i['content']['number'] == issue_number), None)
    if not item:
        print(f"Issue #{issue_number} not found in project.")
        return
    item_id = item['id']
    print(f"Item ID: {item_id}")

    # 3. Update Item
    print(f"Updating Item {item_id} to '{status_value}'...")
    cmd = f"gh project item-edit --id {item_id} --field-id {status_field_id} --project-id {project_id} --single-select-option-id {option_id}"
    update_res = run_command(cmd)
    if update_res:
        print("Update successful.")
    else:
        print("Update failed.")

if __name__ == "__main__":
    main()
