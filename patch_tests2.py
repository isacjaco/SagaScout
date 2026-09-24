import re

with open("tests/test_implementation.py", "r") as f:
    content = f.read()

def unauth_repl(match):
    return match.group(0).replace('headers={"X-API-Key": "test-api-key"}, ', '')

# Find the test_api_unauthorized method and fix it
content = re.sub(
    r'(def test_api_unauthorized\(\):[\s\S]*?assert response\.status_code == 403)',
    unauth_repl,
    content
)

with open("tests/test_implementation.py", "w") as f:
    f.write(content)
