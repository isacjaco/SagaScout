import os

with open("sagascout/api.py", "r") as f:
    content = f.read()

# Add necessary imports
content = content.replace(
    "from fastapi import FastAPI, HTTPException",
    "import os\nfrom fastapi import FastAPI, HTTPException, Security, Depends\nfrom fastapi.security import APIKeyHeader\nfrom fastapi import APIRouter"
)

# Add API Key validation
api_key_code = """
# ---------------------------------------------------------------------------
# Security Configuration
# ---------------------------------------------------------------------------

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    \"\"\"Validate the API Key.\"\"\"
    # In a real app, this should be fetched from environment variables or a secure vault
    # Defaulting to a test key for development/testing if not set
    expected_api_key = os.environ.get("SAGASCOUT_API_KEY", "test-api-key")
    if api_key_header != expected_api_key:
        raise HTTPException(
            status_code=403, detail="Could not validate API Key"
        )
    return api_key_header

# Create a protected router for agent endpoints
protected_router = APIRouter(dependencies=[Depends(get_api_key)])
"""

content = content.replace(
    "# ---------------------------------------------------------------------------\n# Generic request/response models\n# ---------------------------------------------------------------------------",
    api_key_code + "\n# ---------------------------------------------------------------------------\n# Generic request/response models\n# ---------------------------------------------------------------------------"
)

# Replace @app.post with @protected_router.post
content = content.replace("@app.post(", "@protected_router.post(")

# Add router to app at the end
content += "\napp.include_router(protected_router)\n"

with open("sagascout/api.py", "w") as f:
    f.write(content)
