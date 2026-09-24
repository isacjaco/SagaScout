import pytest
import os
from sagascout.persistence import save_agent_state, load_agent_state
from sagascout import Scout


def test_save_agent_state_path_traversal(tmp_path):
    scout = Scout(name="TestScout")

    # Simulate a user providing an absolute path
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()

    malicious_path = str(safe_dir / "../malicious.json")

    # Set DATA_DIR env var to safe_dir
    os.environ["SAGASCOUT_DATA_DIR"] = str(safe_dir)

    with pytest.raises(ValueError) as excinfo:
        save_agent_state(scout, malicious_path)

    assert "Path traversal detected" in str(excinfo.value)

    # Clean up
    del os.environ["SAGASCOUT_DATA_DIR"]


def test_load_agent_state_path_traversal(tmp_path):
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()

    malicious_path = str(safe_dir / "../malicious.json")

    # Set DATA_DIR env var to safe_dir
    os.environ["SAGASCOUT_DATA_DIR"] = str(safe_dir)

    with pytest.raises(ValueError) as excinfo:
        load_agent_state(Scout, malicious_path)

    assert "Path traversal detected" in str(excinfo.value)

    # Clean up
    del os.environ["SAGASCOUT_DATA_DIR"]
