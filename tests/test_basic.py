"""Basic tests for SagaScout agents."""

from sagascout import Scout, Archivist, Oracle, Diplomat
from sagascout.utils import DNAAnalyzer, NarrativeMemory, GovernanceRitual


def test_scout_agent():
    """Test Scout agent basic functionality."""
    scout = Scout(name="TestScout")
    
    match_data = {
        "matches": [
            {"id": "m1", "name": "Test User", "shared_cm": 850, "segments": 15},
        ],
        "threshold_cm": 20,
    }
    
    result = scout.process(match_data)
    
    assert result["total_matches"] == 1
    assert result["cluster_count"] > 0
    assert "summary" in result
    
    print("✓ Scout agent test passed")


def test_archivist_agent():
    """Test Archivist agent basic functionality."""
    archivist = Archivist(name="TestArchivist")
    
    tree_data = {
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "Person 1"},
                {"id": "p2", "name": "Person 2"},
            ],
            "relationships": [
                {"parent": "p1", "child": "p2"},
            ],
        },
    }
    
    result = archivist.process(tree_data)
    
    assert result["status"] == "success"
    assert result["individuals_added"] == 2
    assert result["relationships_added"] == 1
    
    print("✓ Archivist agent test passed")


def test_oracle_agent():
    """Test Oracle agent basic functionality."""
    oracle = Oracle(name="TestOracle")
    
    research_request = {
        "action": "research",
        "query": "test query",
        "languages": ["en"],
        "countries": ["US"],
    }
    
    result = oracle.process(research_request)
    
    assert result["status"] in ["success", "cached"]
    assert "results" in result
    
    print("✓ Oracle agent test passed")


def test_diplomat_agent():
    """Test Diplomat agent basic functionality."""
    diplomat = Diplomat(name="TestDiplomat")
    
    message_request = {
        "action": "draft",
        "recipient": {"id": "r1", "name": "Test Recipient", "country": "US"},
        "purpose": "initial_contact",
        "language": "en",
    }
    
    result = diplomat.process(message_request)
    
    assert result["status"] == "success"
    assert "draft" in result
    assert "recommendations" in result
    
    print("✓ Diplomat agent test passed")


def test_dna_analyzer():
    """Test DNA analyzer utilities."""
    analyzer = DNAAnalyzer()
    
    probabilities = analyzer.calculate_relationship_probability(850, 15)
    assert len(probabilities) > 0
    
    generations = analyzer.estimate_generations(850)
    assert len(generations) == 2
    assert generations[0] > 0
    
    print("✓ DNA analyzer test passed")


def test_narrative_memory():
    """Test narrative memory system."""
    memory = NarrativeMemory()
    
    mem_id = memory.store_memory(
        "test_event",
        {"data": "test"},
        significance=0.8,
        tags=["test"],
    )
    
    assert mem_id is not None
    
    memories = memory.recall_memories(tags=["test"])
    assert len(memories) == 1
    
    print("✓ Narrative memory test passed")


def test_governance_ritual():
    """Test governance ritual system."""
    governance = GovernanceRitual()
    
    ritual_id = governance.create_ritual(
        "Test Ritual",
        "decision",
        ["Agent1", "Agent2"],
        {"threshold": 0.5},
    )
    
    assert ritual_id is not None
    
    decision = governance.council_decision(
        "Test Topic",
        ["Agent1", "Agent2"],
        {"Agent1": "approve", "Agent2": "approve"},
    )
    
    assert decision["outcome"] == "approve"
    
    print("✓ Governance ritual test passed")


def test_agent_memory():
    """Test agent memory functionality."""
    scout = Scout(name="MemoryTestScout")
    
    scout.remember({
        "event": "test_event",
        "data": "test_data",
    })
    
    memories = scout.recall()
    assert len(memories) == 1
    
    status = scout.get_status()
    assert status["memory_count"] == 1
    
    print("✓ Agent memory test passed")


if __name__ == "__main__":
    print("Running SagaScout tests...\n")
    
    test_scout_agent()
    test_archivist_agent()
    test_oracle_agent()
    test_diplomat_agent()
    test_dna_analyzer()
    test_narrative_memory()
    test_governance_ritual()
    test_agent_memory()
    
    print("\n✓ All tests passed!")
