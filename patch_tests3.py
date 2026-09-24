import re

with open("tests/test_implementation.py", "r") as f:
    content = f.read()

content = content.replace("import os\n", "")
content = content.replace("import tempfile\n", "")
content = content.replace("from sagascout.utils import DNAAnalyzer, GovernanceRitual\n", "from sagascout.utils import GovernanceRitual\n")

with open("tests/test_implementation.py", "w") as f:
    f.write(content)
