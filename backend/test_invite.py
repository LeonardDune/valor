import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(".env.production")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Error: Supabase URL or Key not found in .env.production")
    exit(1)

supabase: Client = create_client(url, key)

try:
    print("Testing invite to redirect URL: http://localhost:5173")
    res = supabase.auth.admin.invite_user_by_email(
        "test-invite-" + str(uuid.uuid4())[:8] + "@passmail.com",
        options={"data": {"role": "member"}, "redirect_to": "http://localhost:5173"}
    )
    print("Success:", res)
except Exception as e:
    print("Error:", e)
