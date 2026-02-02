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


def test_genetic_clustering_hierarchical():
    """Test hierarchical clustering in GeneticClustering."""
    from sagascout.utils.dna_analysis import GeneticClustering
    
    matches = [
        {"id": "m1", "shared_cm": 2500},
        {"id": "m2", "shared_cm": 850},
        {"id": "m3", "shared_cm": 150},
        {"id": "m4", "shared_cm": 50},
    ]
    
    result = GeneticClustering.hierarchical_cluster(matches)
    
    assert "clusters" in result
    assert "hierarchy" in result
    assert len(result["clusters"]) > 0
    # Verify the hierarchy structure
    assert "root" in result["hierarchy"]
    assert "immediate_family" in result["hierarchy"]["root"]
    assert "close_family" in result["hierarchy"]["root"]
    assert "extended_family" in result["hierarchy"]["root"]
    assert "distant_relatives" in result["hierarchy"]["root"]
    
    print("✓ Genetic clustering hierarchical test passed")


def test_identify_triangulation_groups():
    """Test triangulation group identification."""
    from sagascout.utils.dna_analysis import GeneticClustering
    
    matches = [
        {"id": "m1", "shared_cm": 850},
        {"id": "m2", "shared_cm": 820},
        {"id": "m3", "shared_cm": 800},
    ]
    
    # Shared matches: m1 shares with m2 and m3; m2 shares with m1 and m3
    shared_matches = {
        "m1": ["m2", "m3"],
        "m2": ["m1", "m3"],
        "m3": ["m1", "m2"],
    }
    
    groups = GeneticClustering.identify_triangulation_groups(matches, shared_matches)
    
    assert len(groups) > 0
    assert isinstance(groups, list)
    # Verify that m1, m2, m3 form a triangulation group
    assert any("m1" in group and "m2" in group for group in groups)
    
    print("✓ Identify triangulation groups test passed")


def test_narrative_memory_get_memory_narrative():
    """Test getting memory narrative with connections."""
    memory = NarrativeMemory()
    
    # Create multiple memories
    mem_id1 = memory.store_memory(
        "discovery",
        {"data": "found ancestor"},
        significance=0.9,
        tags=["discovery"],
    )
    
    mem_id2 = memory.store_memory(
        "research",
        {"data": "archive search"},
        significance=0.7,
        tags=["research"],
    )
    
    # Connect memories
    memory.connect_memories(mem_id1, mem_id2, "leads_to")
    
    # Get narrative
    narrative = memory.get_memory_narrative(mem_id1)
    
    assert "memory" in narrative
    assert "connected_memories" in narrative
    assert "narrative_thread" in narrative
    assert len(narrative["connected_memories"]) == 1
    assert narrative["memory"]["id"] == mem_id1
    
    print("✓ Get memory narrative test passed")


def test_narrative_memory_build_narrative_thread():
    """Test building narrative thread from memories."""
    memory = NarrativeMemory()
    
    # Create a chain of memories
    mem_id1 = memory.store_memory("event1", {"data": "data1"}, 0.8)
    mem_id2 = memory.store_memory("event2", {"data": "data2"}, 0.7)
    mem_id3 = memory.store_memory("event3", {"data": "data3"}, 0.6)
    
    # Connect them in a chain
    memory.connect_memories(mem_id1, mem_id2)
    memory.connect_memories(mem_id2, mem_id3)
    
    # Build narrative thread
    thread = memory._build_narrative_thread(mem_id1, depth=3)
    
    assert len(thread) > 0
    assert thread[0]["id"] == mem_id1
    # Should include connected memories
    assert any(m["id"] == mem_id2 for m in thread)
    
    print("✓ Build narrative thread test passed")


def test_governance_ritual_execute_ritual():
    """Test executing different types of rituals."""
    governance = GovernanceRitual()
    
    # Test decision ritual
    ritual_id = governance.create_ritual(
        "Decision Test",
        "decision",
        ["Agent1", "Agent2", "Agent3"],
        {"threshold": 0.6},
    )
    
    context = {
        "Agent1_vote": "approve",
        "Agent2_vote": "approve",
        "Agent3_vote": "reject",
    }
    
    result = governance.execute_ritual(ritual_id, context)
    
    assert "decision" in result
    assert result["decision"] in ["approved", "rejected"]
    assert "votes" in result
    assert "approval_rate" in result
    
    # Test coordination ritual
    coord_ritual_id = governance.create_ritual(
        "Coordination Test",
        "coordination",
        ["Scout", "Oracle"],
        {},
    )
    
    coord_result = governance.execute_ritual(coord_ritual_id, {"task": "analyze"})
    
    assert coord_result["status"] == "coordinated"
    assert "assignments" in coord_result
    
    # Test review ritual
    review_ritual_id = governance.create_ritual(
        "Review Test",
        "review",
        ["Reviewer1", "Reviewer2"],
        {},
    )
    
    review_result = governance.execute_ritual(review_ritual_id, {"subject": "report"})
    
    assert review_result["status"] == "reviewed"
    assert "reviews" in review_result
    assert "approved" in review_result
    
    print("✓ Execute ritual test passed")


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
    test_genetic_clustering_hierarchical()
    test_identify_triangulation_groups()
    test_narrative_memory_get_memory_narrative()
    test_narrative_memory_build_narrative_thread()
    test_governance_ritual_execute_ritual()
    
    print("\n✓ All tests passed!")