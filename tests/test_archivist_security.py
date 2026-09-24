import pytest
import os
import json
from pathlib import Path
from sagascout.agents.archivist import Archivist

@pytest.fixture
def workspace(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws

@pytest.fixture
def archivist(workspace):
    return Archivist(config={"workspace_dir": str(workspace)})

def test_parse_gedcom_traversal(archivist, workspace):
    # Try to parse a file outside the workspace
    outside_file = workspace.parent / "secret.ged"
    outside_file.write_text("0 HEAD")

    result = archivist.parse_gedcom(str(outside_file))
    assert "error" in result
    assert "Access denied" in result["error"]

def test_parse_gedcom_valid(archivist, workspace):
    # Valid file inside workspace
    inside_file = workspace / "family.ged"
    inside_file.write_text("0 HEAD\n")

    try:
        result = archivist.parse_gedcom(str(inside_file))
        if "error" in result:
            assert "Access denied" not in result["error"]
    except Exception as e:
        assert "Access denied" not in str(e)

def test_export_gedcom_traversal(archivist, workspace):
    outside_file = workspace.parent / "out.ged"
    result = archivist.export_gedcom(str(outside_file))
    assert "error" in result
    assert "Access denied" in result["error"]

def test_export_gedcom_valid(archivist, workspace):
    inside_file = workspace / "out.ged"
    result = archivist.export_gedcom(str(inside_file))
    assert result["status"] == "success"
    assert inside_file.exists()

def test_save_to_file_traversal(archivist, workspace):
    outside_file = workspace.parent / "out.json"
    with pytest.raises(ValueError, match="Access denied"):
        archivist.save_to_file(str(outside_file))

def test_save_to_file_valid(archivist, workspace):
    inside_file = workspace / "out.json"
    archivist.save_to_file(str(inside_file))
    assert inside_file.exists()

def test_load_from_file_traversal(workspace):
    outside_file = workspace.parent / "in.json"
    outside_file.write_text(json.dumps({"individuals": [], "relationships": []}))

    with pytest.raises(ValueError, match="Access denied"):
        Archivist.load_from_file(str(outside_file), config={"workspace_dir": str(workspace)})

def test_load_from_file_valid(workspace):
    inside_file = workspace / "in.json"
    inside_file.write_text(json.dumps({"individuals": [], "relationships": []}))

    archivist = Archivist.load_from_file(str(inside_file), config={"workspace_dir": str(workspace)})
    assert archivist is not None
