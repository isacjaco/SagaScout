"""Example usage of SagaScout agents."""

from sagascout import Scout, Archivist, Oracle, Diplomat
from sagascout.utils import DNAAnalyzer, NarrativeMemory, GovernanceRitual


def example_scout_usage():
    """Demonstrate Scout agent capabilities."""
    print("=== Scout Agent: DNA Match Analysis ===\n")
    
    # Create Scout agent
    scout = Scout(name="ScoutAlpha")
    
    # Sample DNA match data
    match_data = {
        "matches": [
            {"id": "m1", "name": "John Doe", "shared_cm": 3500, "segments": 25},
            {"id": "m2", "name": "Jane Smith", "shared_cm": 850, "segments": 15},
            {"id": "m3", "name": "Bob Wilson", "shared_cm": 250, "segments": 10},
            {"id": "m4", "name": "Alice Brown", "shared_cm": 45, "segments": 5},
        ],
        "threshold_cm": 20,
        "timestamp": "2026-01-31",
    }
    
    # Process DNA matches
    results = scout.process(match_data)
    
    print(f"Total matches: {results['total_matches']}")
    print(f"Clusters found: {results['cluster_count']}")
    print(f"Summary: {results['summary']}\n")
    
    # Analyze individual match
    match_analysis = scout.analyze_match(match_data["matches"][1])
    print(f"Match analysis for {match_analysis['name']}:")
    print(f"  Relationship: {match_analysis['estimated_relationship']}")
    print(f"  Confidence: {match_analysis['confidence']:.1f}%\n")


def example_archivist_usage():
    """Demonstrate Archivist agent capabilities."""
    print("=== Archivist Agent: Family Tree Management ===\n")
    
    # Create Archivist agent
    archivist = Archivist(name="ArchivistBeta")
    
    # Sample family tree data
    tree_data = {
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "George Smith", "birth_year": 1920},
                {"id": "p2", "name": "Mary Smith", "birth_year": 1925},
                {"id": "p3", "name": "John Smith", "birth_year": 1945},
            ],
            "relationships": [
                {"parent": "p1", "child": "p3", "type": "parent"},
                {"parent": "p2", "child": "p3", "type": "parent"},
            ],
        },
    }
    
    # Parse family tree
    result = archivist.process(tree_data)
    print(f"Tree parsing result:")
    print(f"  Individuals: {result['individuals_added']}")
    print(f"  Relationships: {result['relationships_added']}\n")
    
    # Infer relationship
    inference_data = {
        "action": "infer",
        "data": {"person1": "p1", "person2": "p3"},
    }
    
    inference = archivist.process(inference_data)
    print(f"Relationship inference:")
    print(f"  {inference['person1']} → {inference['person2']}")
    print(f"  Relationship: {inference['relationship']}\n")


def example_oracle_usage():
    """Demonstrate Oracle agent capabilities."""
    print("=== Oracle Agent: Multilingual Research ===\n")
    
    # Create Oracle agent
    oracle = Oracle(name="OracleGamma")
    
    # Research request
    research_request = {
        "action": "research",
        "query": "Smith family immigration records",
        "languages": ["en", "de", "fr"],
        "countries": ["US", "DE", "FR"],
    }
    
    # Conduct research
    results = oracle.process(research_request)
    print(f"Research results:")
    print(f"  Query: {results['query']}")
    print(f"  Languages searched: {len(results['languages'])}")
    print(f"  Total sources: {results['total_sources']}\n")
    
    # Search archives
    archive_request = {
        "action": "search_archives",
        "query": "Smith",
        "countries": ["US", "UK", "FR"],
    }
    
    archive_results = oracle.process(archive_request)
    print(f"Archive search results:")
    print(f"  Archives searched: {archive_results['archives_searched']}")
    print(f"  Total records: {archive_results['total_records']}\n")


def example_diplomat_usage():
    """Demonstrate Diplomat agent capabilities."""
    print("=== Diplomat Agent: Cross-Cultural Communication ===\n")
    
    # Create Diplomat agent
    diplomat = Diplomat(name="DiplomatDelta")
    
    # Draft outreach message
    message_request = {
        "action": "draft",
        "recipient": {
            "id": "contact1",
            "name": "Hans Mueller",
            "country": "DE",
        },
        "purpose": "initial_contact",
        "language": "en",
        "context": {"shared_ancestor": "Johann Schmidt"},
    }
    
    # Draft message
    result = diplomat.process(message_request)
    draft = result["draft"]
    
    print(f"Drafted message:")
    print(f"  To: {draft['recipient']['name']}")
    print(f"  Subject: {draft['subject']}")
    print(f"  Tone: {draft['tone']}\n")
    print(f"Message body:\n{draft['body']}\n")
    
    print(f"Recommendations:")
    for rec in result["recommendations"]:
        print(f"  - {rec}")
    print()
    
    # Analyze cultural context
    culture_request = {
        "action": "analyze_culture",
        "country": "JP",
        "situation": "initial_contact",
    }
    
    culture_analysis = diplomat.process(culture_request)
    print(f"Cultural analysis for Japan:")
    analysis = culture_analysis["analysis"]
    print(f"  Communication style: {analysis['communication_style']}")
    print(f"  Formality level: {analysis['formality_level']}\n")


def example_utilities():
    """Demonstrate utility functions."""
    print("=== Utility Functions ===\n")
    
    # DNA Analysis
    print("DNA Analysis:")
    analyzer = DNAAnalyzer()
    probabilities = analyzer.calculate_relationship_probability(850, 15)
    print(f"  Shared cM: 850")
    for rel, prob in list(probabilities.items())[:3]:
        print(f"    {rel}: {prob:.2%}")
    print()
    
    # Narrative Memory
    print("Narrative Memory:")
    memory = NarrativeMemory()
    
    mem_id = memory.store_memory(
        "discovery",
        {"finding": "Located birth record", "person": "John Smith"},
        significance=0.8,
        tags=["research", "breakthrough"],
    )
    print(f"  Stored memory: {mem_id}")
    
    memories = memory.recall_memories(tags=["research"], min_significance=0.5)
    print(f"  Recalled {len(memories)} memories\n")
    
    # Governance Ritual
    print("Governance Ritual:")
    governance = GovernanceRitual()
    
    ritual_id = governance.create_ritual(
        "Research Approval",
        "decision",
        ["Scout", "Archivist", "Oracle"],
        {"threshold": 0.66},
    )
    print(f"  Created ritual: {ritual_id}")
    
    decision = governance.council_decision(
        "Expand research to Germany",
        ["Scout", "Archivist", "Oracle"],
        {"Scout": "approve", "Archivist": "approve", "Oracle": "approve"},
    )
    print(f"  Decision outcome: {decision['outcome']}\n")


def example_ecosystem_coordination():
    """Demonstrate coordinated ecosystem usage."""
    print("=== Ecosystem Coordination ===\n")
    
    # Create all agents
    scout = Scout(name="Scout-1")
    archivist = Archivist(name="Archivist-1")
    oracle = Oracle(name="Oracle-1")
    diplomat = Diplomat(name="Diplomat-1")
    
    print("Step 1: Scout analyzes DNA matches")
    match_data = {
        "matches": [
            {"id": "m1", "name": "Maria Garcia", "shared_cm": 850, "segments": 15},
        ],
        "threshold_cm": 20,
    }
    scout_result = scout.process(match_data)
    print(f"  Found {scout_result['total_matches']} matches\n")
    
    print("Step 2: Oracle researches the Garcia family")
    research_request = {
        "action": "research",
        "query": "Garcia family Spain",
        "languages": ["en", "es"],
        "countries": ["ES"],
    }
    oracle_result = oracle.process(research_request)
    print(f"  Found {oracle_result['total_sources']} sources\n")
    
    print("Step 3: Archivist integrates findings into family tree")
    tree_data = {
        "action": "parse",
        "data": {
            "individuals": [
                {"id": "p1", "name": "Maria Garcia", "birth_year": 1985},
            ],
            "relationships": [],
        },
    }
    archivist_result = archivist.process(tree_data)
    print(f"  Added {archivist_result['individuals_added']} individuals\n")
    
    print("Step 4: Diplomat drafts outreach message")
    message_request = {
        "action": "draft",
        "recipient": {
            "id": "m1",
            "name": "Maria Garcia",
            "country": "ES",
        },
        "purpose": "initial_contact",
        "language": "en",
    }
    diplomat_result = diplomat.process(message_request)
    print(f"  Message drafted with tone: {diplomat_result['draft']['tone']}\n")
    
    print("Ecosystem coordination complete! All agents worked together.\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SagaScout: Autonomous Lineage Intelligence")
    print("Example Usage Demonstrations")
    print("=" * 60)
    print()
    
    example_scout_usage()
    print("-" * 60)
    print()
    
    example_archivist_usage()
    print("-" * 60)
    print()
    
    example_oracle_usage()
    print("-" * 60)
    print()
    
    example_diplomat_usage()
    print("-" * 60)
    print()
    
    example_utilities()
    print("-" * 60)
    print()
    
    example_ecosystem_coordination()
    print("=" * 60)
