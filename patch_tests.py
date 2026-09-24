import re

with open("tests/test_implementation.py", "r") as f:
    content = f.read()

# Fix the test_api_unauthorized where it accidentally added the header
content = content.replace(
    'response = client.post("/scout/analyze", headers={"X-API-Key": "test-api-key"}, json={\n            "payload": {\n                "matches": [],\n                "threshold_cm": 20\n            }\n        })\n        # By default fastapi raises 403 when API key header is missing\n        assert response.status_code == 403',
    'response = client.post("/scout/analyze", json={\n            "payload": {\n                "matches": [],\n                "threshold_cm": 20\n            }\n        })\n        # By default fastapi raises 403 when API key header is missing\n        assert response.status_code == 403'
)

with open("tests/test_implementation.py", "w") as f:
    f.write(content)
