import os
from dotenv import load_dotenv

load_dotenv()

print("--- Environment Variable Check ---")
print(f"GOOGLE_CLIENT_ID: {'[SET]' if os.getenv('GOOGLE_CLIENT_ID') else '[MISSING]'}")
print(f"GOOGLE_CLIENT_SECRET: {'[SET]' if os.getenv('GOOGLE_CLIENT_SECRET') else '[MISSING]'}")
print(f"GITHUB_CLIENT_ID: {'[SET]' if os.getenv('GITHUB_CLIENT_ID') else '[MISSING]'}")
print(f"BACKEND_URL: {os.getenv('BACKEND_URL', 'Not set (using default)')}")
print(f"FRONTEND_URL: {os.getenv('FRONTEND_URL', 'Not set (using default)')}")
