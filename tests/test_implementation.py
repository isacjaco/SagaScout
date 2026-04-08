"""
Expanded test suite covering:
- Diplomat: send_message, respond_to_message, analyze_cultural_context
- Negative/invalid-input tests for Oracle, Scout, Archivist, GovernanceRitual
- Archivist merge conflict detection
- Oracle archive search determinism
- Scout: find_shared_matches_from_data, CSV import, serialization
- Archivist: GEDCOM export/import, JSON serialization
- NarrativeMemory: serialization
- Persistence module
- CLI smoke tests
- FastAPI endpoints smoke tests
"""

import json
import os
import tempfile

import pytest

from sagascout import Scout, Archivist, Oracle, Diplomat
from sagascout.utils import DNAAnalyzer, NarrativeMemory, GovernanceRitual
from sagascout.persistence import save_agent_state, load_agent_state


# ---------------------------------------------------------------------------
# Diplomat: send_message
# ---------------------------------------------------------------------------

def test_diplomat_send_message():
    """Test Diplomat.send_message records communication and updates contact."""
    diplomat = Diplomat(name="TestDiplomat")
    result = diplomat.process({
        "action": "send",
        "message": {
            "recipient": {"id": "r1", "name": "Alice"},
            "subject": "Hello",
            "body": "Test body",
        },
        "timestamp": "2026-01-01T00:00:00",
    })
    assert result["status"] == "success"
    assert "communication_id" in result
    assert result["recipient_id"] == "r1"

    # Verify contact tracked
    contact = diplomat.get_contact_info("r1")
    assert contact is not None
    assert contact["messages_sent"] == 1

    # Verify history
    history = diplomat.get_communication_history("r1")
    assert len(history) == 1


def test_diplomat_respond_to_message():
    """Test Diplomat.respond_to_message generates a contextual response."""
    diplomat = Diplomat(name="TestDiplomat")

    # Question intent
    result = diplomat.process({
        "action": "respond",
        "original_message": {
            "text": "Do you have records for the Johnson family?",
            "subject": "Family History Question",
            "language": "en",
        },
        "tone": "friendly",
    })
    assert result["status"] == "success"
    assert "response" in result
    assert "analysis" in result
    assert result["analysis"]["intent"] == "question"

    # Information-sharing intent
    result2 = diplomat.process({
        "action": "respond",
        "original_message": {
            "text": "I found and discovered some great records.",
            "subject": "New Findings",
            "language": "en",
        },
    })
    assert result2["analysis"]["intent"] == "information_sharing"


def test_diplomat_analyze_cultural_context_known():
    """Test analyze_cultural_context returns profile for known country."""
    diplomat = Diplomat(name="TestDiplomat")
    result = diplomat.process({
        "action": "analyze_culture",
        "country": "JP",
        "situation": "general",
    })
    assert result["status"] == "success"
    assert result["analysis"]["country"] == "JP"
    assert result["analysis"]["formality_level"] == "high"
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) > 0


def test_diplomat_analyze_cultural_context_unknown():
    """Test analyze_cultural_context gracefully handles unknown country."""
    diplomat = Diplomat(name="TestDiplomat")
    result = diplomat.process({
        "action": "analyze_culture",
        "country": "ZZ",
    })
    assert result["status"] == "limited"
    assert "message" in result


def test_diplomat_invalid_action():
    """Test Diplomat.process returns error for unknown action."""
    diplomat = Diplomat(name="TestDiplomat")
    result = diplomat.process({"action": "nonexistent"})
    assert "error" in result


# ---------------------------------------------------------------------------
# Oracle: negative / invalid-input tests
# ---------------------------------------------------------------------------

def test_oracle_invalid_action():
    """Test Oracle.process returns error for unknown action."""
    oracle = Oracle(name="TestOracle")
    result = oracle.process({"action": "fly_to_the_moon"})
    assert "error" in result


def test_oracle_research_unsupported_language():
    """Test Oracle.research silently skips unsupported languages."""
    oracle = Oracle(name="TestOracle")
    result = oracle.process({
        "action": "research",
        "query": "test",
        "languages": ["xx"],  # unsupported
    })
    assert result["status"] == "success"
    assert result["results"] == []


def test_oracle_archive_search_deterministic():
    """Test that archive search returns the same value across calls."""
    oracle = Oracle(name="TestOracle", config={"archive_search_result_count": 7})
    result1 = oracle.process({
        "action": "search_archives",
        "query": "Smith",
        "countries": ["US"],
    })
    result2 = oracle.process({
        "action": "search_archives",
        "query": "Smith",
        "countries": ["US"],
    })
    counts_1 = [r["records_found"] for r in result1["results"]]
    counts_2 = [r["records_found"] for r in result2["results"]]
    assert counts_1 == counts_2
    assert all(c == 7 for c in counts_1)


def test_oracle_archive_search_hash_deterministic():
    """Test that default (hash-based) archive stub is stable without config."""
    oracle = Oracle(name="TestOracle")
    result1 = oracle.process({
        "action": "search_archives",
        "query": "Jones",
        "countries": ["UK"],
    })
    result2 = oracle.process({
        "action": "search_archives",
        "query": "Jones",
        "countries": ["UK"],
    })
    assert [r["records_found"] for r in result1["results"]] == \
           [r["records_found"] for r in result2["results"]]


def test_oracle_translate_stub():
    """Test stub translation prefixes language code."""
    oracle = Oracle(name="TestOracle")
    result = oracle.process({
        "action": "translate",
        "query": "family",
        "languages": ["de", "fr"],
    })
    assert result["status"] == "success"
    assert result["translations"]["de"]["translated"] == "[de] family"
    assert result["translations"]["fr"]["translated"] == "[fr] family"


# ---------------------------------------------------------------------------
# Scout: negative tests, find_shared_matches_from_data, serialization
# ---------------------------------------------------------------------------

def test_scout_find_shared_matches_from_data():
    """Test find_shared_matches_from_data returns intersection of shared matches."""
    scout = Scout(name="TestScout")
    scout.matches = [
        {"id": "m1", "shared_cm": 500},
        {"id": "m2", "shared_cm": 400},
        {"id": "m3", "shared_cm": 300},
        {"id": "m4", "shared_cm": 200},
    ]
    shared_map = {
        "m1": ["m2", "m3"],
        "m2": ["m1", "m3", "m4"],
    }
    shared = scout.find_shared_matches_from_data("m1", "m2", shared_map)
    shared_ids = {m["id"] for m in shared}
    assert shared_ids == {"m3"}


def test_scout_find_shared_matches_empty():
    """Test find_shared_matches_from_data returns empty list when no overlap."""
    scout = Scout(name="TestScout")
    scout.matches = [{"id": "m1"}, {"id": "m2"}]
    result = scout.find_shared_matches_from_data("m1", "m2", {})
    assert result == []


def test_scout_csv_import_ancestry(tmp_path):
    """Test AncestryDNA CSV import."""
    csv_content = (
        "Match Name,Shared DNA,Shared Segments\n"
        "Alice Smith,850 cM,15\n"
        "Bob Jones,200 cM,5\n"
    )
    csv_file = tmp_path / "ancestry.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    scout = Scout(name="TestScout")
    result = scout.import_ancestry_csv(str(csv_file))
    assert result["status"] == "success"
    assert result["imported"] == 2
    assert len(scout.matches) == 2
    assert scout.matches[0]["shared_cm"] == 850.0
    assert scout.matches[0]["source"] == "ancestry"


def test_scout_csv_import_ancestry_missing_file():
    """Test AncestryDNA CSV import with missing file."""
    scout = Scout(name="TestScout")
    result = scout.import_ancestry_csv("/nonexistent/file.csv")
    assert "error" in result


def test_scout_csv_import_23andme(tmp_path):
    """Test 23andMe CSV import."""
    csv_content = (
        "Name,DNA Shared,Segments\n"
        "Carol Brown,700,12\n"
    )
    csv_file = tmp_path / "23andme.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    scout = Scout(name="TestScout")
    result = scout.import_23andme_csv(str(csv_file))
    assert result["status"] == "success"
    assert result["imported"] == 1
    assert scout.matches[0]["shared_cm"] == 700.0
    assert scout.matches[0]["source"] == "23andme"


def test_scout_serialization_roundtrip():
    """Test Scout to_json / from_json round-trip."""
    scout = Scout(name="TestScout")
    scout.matches = [{"id": "m1", "shared_cm": 850, "segments": 15}]
    scout.clusters = {"1st_2nd_cousins": [{"id": "m1"}]}

    data = scout.to_json()
    restored = Scout.from_json(data, name="Restored")
    assert restored.matches == scout.matches
    assert restored.clusters == scout.clusters


def test_scout_save_load_file(tmp_path):
    """Test Scout save_to_file / load_from_file."""
    scout = Scout(name="TestScout")
    scout.matches = [{"id": "m1", "shared_cm": 200, "segments": 5}]
    filepath = str(tmp_path / "scout.json")
    scout.save_to_file(filepath)

    loaded = Scout.load_from_file(filepath, name="Loaded")
    assert loaded.matches == scout.matches


# ---------------------------------------------------------------------------
# Archivist: merge conflict, serialization, GEDCOM export
# ---------------------------------------------------------------------------

def test_archivist_merge_conflict_detection():
    """Test that merge_trees detects conflicting field values."""
    archivist = Archivist(name="TestArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "John Doe", "birth_date": "1900-01-01"},
            ],
            "relationships": [],
        },
    })

    # Merge with conflicting birth_date
    result = archivist.process({
        "action": "merge",
        "data": {
            "individuals": [
                {"id": "p1", "name": "John Doe", "birth_date": "1905-06-15"},
            ],
            "relationships": [],
        },
    })
    assert result["status"] == "success"
    assert len(result["conflicts"]) == 1
    conflict = result["conflicts"][0]
    assert conflict["person_id"] == "p1"
    assert "birth_date" in conflict["conflicts"]


def test_archivist_merge_no_conflict():
    """Test that merge_trees with same data produces no conflicts."""
    archivist = Archivist(name="TestArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [{"id": "p1", "name": "Jane"}],
            "relationships": [],
        },
    })
    result = archivist.process({
        "action": "merge",
        "data": {
            "individuals": [{"id": "p1", "name": "Jane"}],
            "relationships": [],
        },
    })
    assert result["conflicts"] == []


def test_archivist_invalid_action():
    """Test Archivist returns error for unknown action."""
    archivist = Archivist(name="TestArchivist")
    result = archivist.process({"action": "teleport"})
    assert "error" in result


def test_archivist_serialization_roundtrip():
    """Test Archivist to_json / from_json round-trip."""
    archivist = Archivist(name="TestArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "Alice"},
                {"id": "p2", "name": "Bob"},
            ],
            "relationships": [{"parent": "p1", "child": "p2"}],
        },
    })
    data = archivist.to_json()
    restored = Archivist.from_json(data, name="Restored")
    assert set(restored.individuals.keys()) == {"p1", "p2"}
    assert restored.tree.has_edge("p1", "p2")


def test_archivist_save_load_file(tmp_path):
    """Test Archivist save_to_file / load_from_file."""
    archivist = Archivist(name="TestArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [{"id": "x1", "name": "Eve"}],
            "relationships": [],
        },
    })
    filepath = str(tmp_path / "archivist.json")
    archivist.save_to_file(filepath)

    loaded = Archivist.load_from_file(filepath, name="Loaded")
    assert "x1" in loaded.individuals


def test_archivist_gedcom_export(tmp_path):
    """Test GEDCOM export produces a valid-looking .ged file."""
    archivist = Archivist(name="TestArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "I1", "name": "John Smith", "birth_date": "1900-01-01"},
                {"id": "I2", "name": "Jane Smith"},
            ],
            "relationships": [{"parent": "I1", "child": "I2"}],
        },
    })
    gedcom_path = str(tmp_path / "tree.ged")
    result = archivist.export_gedcom(gedcom_path)
    assert result["status"] == "success"
    content = open(gedcom_path, encoding="utf-8").read()
    assert "0 HEAD" in content
    assert "INDI" in content
    assert "John Smith" in content
    assert "0 TRLR" in content


def test_archivist_gedcom_parse_missing_file():
    """Test parse_gedcom with missing file returns error."""
    archivist = Archivist(name="TestArchivist")
    result = archivist.parse_gedcom("/nonexistent/tree.ged")
    assert "error" in result


# ---------------------------------------------------------------------------
# NarrativeMemory: serialization
# ---------------------------------------------------------------------------

def test_narrative_memory_serialization_roundtrip():
    """Test NarrativeMemory to_json / from_json round-trip."""
    nm = NarrativeMemory()
    mid1 = nm.store_memory("discovery", {"data": "found ancestor"}, significance=0.9)
    mid2 = nm.store_memory("research", {"data": "archive search"}, significance=0.7)
    nm.connect_memories(mid1, mid2, "leads_to")

    data = nm.to_json()
    restored = NarrativeMemory.from_json(data)

    assert len(restored.memories) == 2
    assert restored.memory_connections[mid1] == [mid2]
    retrieved = restored.recall_memories(event_type="discovery")
    assert len(retrieved) == 1


def test_narrative_memory_save_load_file(tmp_path):
    """Test NarrativeMemory save_to_file / load_from_file."""
    nm = NarrativeMemory()
    nm.store_memory("event", {"data": "test"}, significance=0.5, tags=["test"])
    filepath = str(tmp_path / "memory.json")
    nm.save_to_file(filepath)

    loaded = NarrativeMemory.load_from_file(filepath)
    memories = loaded.recall_memories(tags=["test"])
    assert len(memories) == 1


# ---------------------------------------------------------------------------
# Persistence module
# ---------------------------------------------------------------------------

def test_persistence_scout(tmp_path):
    """Test save_agent_state / load_agent_state for Scout."""
    scout = Scout(name="MyScout")
    scout.matches = [{"id": "m1", "shared_cm": 500}]
    filepath = str(tmp_path / "scout_state.json")
    save_agent_state(scout, filepath)
    restored = load_agent_state(Scout, filepath)
    assert restored.name == "MyScout"
    assert restored.matches == scout.matches


def test_persistence_archivist(tmp_path):
    """Test save_agent_state / load_agent_state for Archivist."""
    archivist = Archivist(name="MyArchivist")
    archivist.process({
        "action": "parse",
        "data": {
            "individuals": [{"id": "p1", "name": "Alice"}],
            "relationships": [],
        },
    })
    filepath = str(tmp_path / "archivist_state.json")
    save_agent_state(archivist, filepath)
    restored = load_agent_state(Archivist, filepath)
    assert restored.name == "MyArchivist"
    assert "p1" in restored.individuals


def test_persistence_narrative_memory(tmp_path):
    """Test save_agent_state / load_agent_state for NarrativeMemory."""
    nm = NarrativeMemory()
    nm.store_memory("test", {"data": "x"}, significance=0.8)
    filepath = str(tmp_path / "nm_state.json")
    save_agent_state(nm, filepath)
    restored = load_agent_state(NarrativeMemory, filepath)
    assert len(restored.memories) == 1


def test_persistence_unsupported_type():
    """Test save_agent_state raises TypeError for unsupported types."""
    with pytest.raises(TypeError):
        save_agent_state(object(), "/tmp/test.json")


def test_persistence_load_unsupported_class(tmp_path):
    """Test load_agent_state raises TypeError for unsupported classes."""
    filepath = str(tmp_path / "dummy.json")
    with open(filepath, "w") as f:
        json.dump({}, f)
    with pytest.raises(TypeError):
        load_agent_state(object, filepath)


# ---------------------------------------------------------------------------
# GovernanceRitual: unknown ritual type
# ---------------------------------------------------------------------------

def test_governance_unknown_ritual_type():
    """Test execute_ritual returns error for unknown ritual type."""
    gov = GovernanceRitual()
    ritual_id = gov.create_ritual("Bad", "dance", ["A"], {})
    result = gov.execute_ritual(ritual_id, {})
    assert "error" in result


def test_governance_ritual_not_found():
    """Test execute_ritual returns error for nonexistent ritual ID."""
    gov = GovernanceRitual()
    result = gov.execute_ritual("ritual_999", {})
    assert "error" in result


# ---------------------------------------------------------------------------
# GovernanceRitual imported from governance module (new home)
# ---------------------------------------------------------------------------

def test_governance_ritual_import_path():
    """Test that GovernanceRitual is importable from the new module."""
    from sagascout.utils.governance import GovernanceRitual as GR
    assert GR is GovernanceRitual


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------

def test_cli_scout_analyze_empty(capsys):
    """Test CLI scout analyze with no matches returns valid JSON."""
    from sagascout.__main__ import build_parser, _cmd_scout
    parser = build_parser()
    args = parser.parse_args(["scout", "analyze"])
    _cmd_scout(args)
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["total_matches"] == 0


def test_cli_oracle_research(capsys):
    """Test CLI oracle research returns JSON."""
    from sagascout.__main__ import build_parser, _cmd_oracle
    parser = build_parser()
    args = parser.parse_args(["oracle", "research", "--query", "Smith"])
    _cmd_oracle(args)
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["status"] == "success"


def test_cli_diplomat_draft(capsys):
    """Test CLI diplomat draft returns JSON."""
    from sagascout.__main__ import build_parser, _cmd_diplomat
    parser = build_parser()
    args = parser.parse_args([
        "diplomat", "draft",
        "--recipient", '{"id": "r1", "country": "US"}',
        "--purpose", "initial_contact",
    ])
    _cmd_diplomat(args)
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["status"] == "success"


# ---------------------------------------------------------------------------
# FastAPI smoke tests
# ---------------------------------------------------------------------------

def test_api_health():
    """Test /health endpoint returns ok."""
    from fastapi.testclient import TestClient
    from sagascout.api import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_scout_analyze():
    """Test /scout/analyze endpoint."""
    from fastapi.testclient import TestClient
    from sagascout.api import app
    client = TestClient(app)
    response = client.post("/scout/analyze", json={
        "payload": {
            "matches": [{"id": "m1", "shared_cm": 850, "segments": 15}],
            "threshold_cm": 20,
        }
    })
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["total_matches"] == 1


def test_api_oracle_research():
    """Test /oracle/research endpoint."""
    from fastapi.testclient import TestClient
    from sagascout.api import app
    client = TestClient(app)
    response = client.post("/oracle/research", json={
        "payload": {"query": "Jones family", "languages": ["en"]}
    })
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"


def test_api_diplomat_draft():
    """Test /diplomat/draft endpoint."""
    from fastapi.testclient import TestClient
    from sagascout.api import app
    client = TestClient(app)
    response = client.post("/diplomat/draft", json={
        "payload": {
            "recipient": {"id": "r1", "country": "US"},
            "purpose": "initial_contact",
            "language": "en",
        }
    })
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"


def test_api_archivist_parse():
    """Test /archivist/parse endpoint."""
    from fastapi.testclient import TestClient
    from sagascout.api import app
    client = TestClient(app)
    response = client.post("/archivist/parse", json={
        "payload": {
            "individuals": [{"id": "p1", "name": "Alice"}],
            "relationships": [],
        }
    })
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
