"""Tests for refactored code to ensure no duplication introduced bugs."""

from sagascout import Scout, Archivist, Oracle
from sagascout.utils import DNAAnalyzer, GovernanceRitual


def test_dna_analyzer_estimate_relationship():
    """Test the new estimate_relationship method in DNAAnalyzer."""
    analyzer = DNAAnalyzer()
    
    # Test various cM ranges
    assert analyzer.estimate_relationship(3600) == "Parent/Child or Identical Twin"
    assert analyzer.estimate_relationship(2500) == "Sibling or Grandparent/Grandchild"
    assert analyzer.estimate_relationship(1500) == "Half Sibling or Uncle/Aunt"
    assert analyzer.estimate_relationship(800) == "1st Cousin or Great-Grandparent"
    assert analyzer.estimate_relationship(250) == "1st-2nd Cousin"
    assert analyzer.estimate_relationship(120) == "2nd-3rd Cousin"
    assert analyzer.estimate_relationship(50) == "3rd-4th Cousin"
    assert analyzer.estimate_relationship(10) == "Distant Cousin"
    
    print("✓ DNAAnalyzer estimate_relationship test passed")


def test_scout_uses_dna_analyzer():
    """Test that Scout correctly uses DNAAnalyzer for relationship estimation."""
    scout = Scout(name="TestScout")
    
    match_data = {
        "id": "m1",
        "name": "Test Match",
        "shared_cm": 850,
        "segments": 15,
    }
    
    result = scout.analyze_match(match_data)
    
    assert result["estimated_relationship"] == "1st Cousin or Great-Grandparent"
    assert result["shared_cm"] == 850
    assert result["segments"] == 15
    
    print("✓ Scout uses DNAAnalyzer test passed")


def test_oracle_document_extraction_refactored():
    """Test that Oracle document extraction still works after refactoring."""
    oracle = Oracle(name="TestOracle")
    
    # Test birth record extraction
    birth_doc = {
        "id": "birth1",
        "name": "John Doe",
        "date": "1950-01-01",
        "place": "New York",
        "parents": ["Parent1", "Parent2"],
    }
    
    birth_result = oracle.process({
        "action": "extract",
        "document": birth_doc,
        "type": "birth_record",
    })
    
    assert birth_result["status"] == "success"
    assert birth_result["extracted"]["data"]["record_type"] == "birth"
    assert birth_result["extracted"]["data"]["name"] == "John Doe"
    assert birth_result["extracted"]["data"]["birth_date"] == "1950-01-01"
    assert birth_result["extracted"]["data"]["birth_place"] == "New York"
    assert birth_result["extracted"]["data"]["parents"] == ["Parent1", "Parent2"]
    
    # Test death record extraction
    death_doc = {
        "id": "death1",
        "name": "Jane Doe",
        "date": "2020-12-31",
        "place": "California",
        "age": 70,
    }
    
    death_result = oracle.process({
        "action": "extract",
        "document": death_doc,
        "type": "death_record",
    })
    
    assert death_result["status"] == "success"
    assert death_result["extracted"]["data"]["record_type"] == "death"
    assert death_result["extracted"]["data"]["name"] == "Jane Doe"
    assert death_result["extracted"]["data"]["death_date"] == "2020-12-31"
    assert death_result["extracted"]["data"]["age"] == 70
    
    # Test marriage record extraction
    marriage_doc = {
        "id": "marriage1",
        "spouse1": "John Smith",
        "spouse2": "Mary Johnson",
        "date": "1975-06-15",
        "place": "Texas",
    }
    
    marriage_result = oracle.process({
        "action": "extract",
        "document": marriage_doc,
        "type": "marriage_record",
    })
    
    assert marriage_result["status"] == "success"
    assert marriage_result["extracted"]["data"]["record_type"] == "marriage"
    assert marriage_result["extracted"]["data"]["spouse1"] == "John Smith"
    assert marriage_result["extracted"]["data"]["spouse2"] == "Mary Johnson"
    
    # Test census record extraction
    census_doc = {
        "id": "census1",
        "year": 1920,
        "household": ["Person1", "Person2"],
        "location": "Illinois",
    }
    
    census_result = oracle.process({
        "action": "extract",
        "document": census_doc,
        "type": "census",
    })
    
    assert census_result["status"] == "success"
    assert census_result["extracted"]["data"]["record_type"] == "census"
    assert census_result["extracted"]["data"]["year"] == 1920
    assert len(census_result["extracted"]["data"]["household"]) == 2
    
    print("✓ Oracle document extraction test passed")


def test_archivist_person_validation():
    """Test that Archivist validation works after refactoring."""
    archivist = Archivist(name="TestArchivist")
    
    # Add some people to the tree
    tree_data = {
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "Person 1"},
                {"id": "p2", "name": "Person 2"},
                {"id": "p3", "name": "Person 3"},
            ],
            "relationships": [
                {"parent": "p1", "child": "p2"},
                {"parent": "p1", "child": "p3"},
            ],
        },
    }
    
    archivist.process(tree_data)
    
    # Test successful queries
    ancestors_result = archivist.process({
        "action": "query",
        "data": {"type": "ancestors", "person_id": "p2"},
    })
    
    assert "error" not in ancestors_result
    assert ancestors_result["person_id"] == "p2"
    assert "p1" in ancestors_result["ancestors"]
    
    descendants_result = archivist.process({
        "action": "query",
        "data": {"type": "descendants", "person_id": "p1"},
    })
    
    assert "error" not in descendants_result
    assert descendants_result["person_id"] == "p1"
    assert len(descendants_result["descendants"]) == 2
    
    siblings_result = archivist.process({
        "action": "query",
        "data": {"type": "siblings", "person_id": "p2"},
    })
    
    assert "error" not in siblings_result
    assert siblings_result["person_id"] == "p2"
    assert "p3" in siblings_result["siblings"]
    
    # Test error handling for non-existent person
    error_result = archivist.process({
        "action": "query",
        "data": {"type": "ancestors", "person_id": "p999"},
    })
    
    assert error_result["error"] == "Person not found"
    
    print("✓ Archivist validation test passed")


def test_governance_coordination_mapping():
    """Test that governance coordination ritual uses mapping correctly."""
    governance = GovernanceRitual()
    
    # Create a coordination ritual with various agent types
    ritual_id = governance.create_ritual(
        "Test Coordination",
        "coordination",
        ["Scout_Agent_1", "Archivist_Agent_2", "Oracle_Agent_3", "Diplomat_Agent_4"],
        {},
    )
    
    result = governance.execute_ritual(ritual_id, {})
    
    assert result["status"] == "coordinated"
    assert "assignments" in result
    
    # Verify correct role assignments
    assert result["assignments"]["Scout_Agent_1"] == "dna_analysis"
    assert result["assignments"]["Archivist_Agent_2"] == "tree_management"
    assert result["assignments"]["Oracle_Agent_3"] == "research"
    assert result["assignments"]["Diplomat_Agent_4"] == "communication"
    
    print("✓ Governance coordination mapping test passed")


def test_oracle_extraction_with_missing_fields():
    """Test Oracle extraction handles missing fields correctly."""
    oracle = Oracle(name="TestOracle")
    
    # Test with incomplete document
    incomplete_doc = {
        "id": "incomplete1",
        "name": "John Doe",
        # Missing date and place
    }
    
    result = oracle.process({
        "action": "extract",
        "document": incomplete_doc,
        "type": "birth_record",
    })
    
    assert result["status"] == "success"
    assert result["extracted"]["data"]["name"] == "John Doe"
    assert result["extracted"]["data"]["birth_date"] is None
    assert result["extracted"]["data"]["birth_place"] is None
    assert result["extracted"]["data"]["parents"] == []  # Default empty list
    
    print("✓ Oracle extraction with missing fields test passed")


if __name__ == "__main__":
    print("Running refactored code tests...\n")
    
    test_dna_analyzer_estimate_relationship()
    test_scout_uses_dna_analyzer()
    test_oracle_document_extraction_refactored()
    test_archivist_person_validation()
    test_governance_coordination_mapping()
    test_oracle_extraction_with_missing_fields()
    
    print("\n✓ All refactored code tests passed!")
