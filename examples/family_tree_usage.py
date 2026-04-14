"""
Family Tree Agent System — End-to-End Usage Example

Demonstrates the full SagaScout family-tree agent workflow:

1. Import a family tree from GEDCOM (.ged) or JSON format.
2. Build a hierarchical agent structure (one agent per person, scouts at
   the oldest known generation of each lineage).
3. Run a discovery cycle in which:
   - Knowledge is distilled and passed from the youngest generation upward.
   - Scouts receive the accumulated briefing and search for new relatives.
   - Discovery reports flow back down to the tree manager.
4. Inspect individual node agents for per-person details.
"""

import json
import os
import tempfile

from sagascout import FamilyTreeManager, LineageScoutAgent
from sagascout.utils import GEDCOMImporter, JSONImporter, load_tree


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_GEDCOM = """\
0 HEAD
1 SOUR SagaScout
0 @I1@ INDI
1 NAME Johann /Schmidt/
1 SEX M
1 BIRT
2 DATE 12 MAR 1820
2 PLAC Bavaria, Germany
1 OCCU Farmer
1 NOTE Arrived New York 1855
0 @I2@ INDI
1 NAME Helga /Braun/
1 SEX F
1 BIRT
2 DATE 3 JUL 1825
2 PLAC Saxony, Germany
0 @I3@ INDI
1 NAME Karl /Schmidt/
1 SEX M
1 BIRT
2 DATE 8 NOV 1850
2 PLAC New York, USA
0 @I4@ INDI
1 NAME Rosa /Muller/
1 SEX F
1 BIRT
2 DATE 22 FEB 1855
2 PLAC Hamburg, Germany
0 @I5@ INDI
1 NAME Heinrich /Schmidt/
1 SEX M
1 BIRT
2 DATE 14 JAN 1880
2 PLAC Chicago, USA
0 @I6@ INDI
1 NAME Emma /Schmidt/
1 SEX F
1 BIRT
2 DATE 30 DEC 1910
2 PLAC Chicago, USA
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 5 JUN 1845
2 PLAC Munich, Germany
0 @F2@ FAM
1 HUSB @I3@
1 WIFE @I4@
1 CHIL @I5@
1 MARR
2 DATE 20 OCT 1875
2 PLAC New York, USA
0 @F3@ FAM
1 HUSB @I5@
1 CHIL @I6@
0 TRLR
"""

SAMPLE_JSON = [
    {"id": "A1", "name": "Colm O'Brien",  "sex": "M", "birth_date": "1840", "birth_place": "Galway, Ireland"},
    {"id": "A2", "name": "Brigid Murphy", "sex": "F", "birth_date": "1845", "birth_place": "Mayo, Ireland"},
    {"id": "B1", "name": "Patrick O'Brien", "sex": "M", "birth_date": "1870",
     "birth_place": "Boston, USA", "father_id": "A1", "mother_id": "A2"},
    {"id": "C1", "name": "Sean O'Brien", "sex": "M", "birth_date": "1900",
     "birth_place": "Boston, USA", "father_id": "B1"},
]


# ---------------------------------------------------------------------------
# Example 1: Import from GEDCOM
# ---------------------------------------------------------------------------

def example_gedcom_import():
    print("=" * 60)
    print("Example 1: Import from GEDCOM (.ged)")
    print("=" * 60)

    # Write GEDCOM to a temp file to mimic real usage
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ged", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_GEDCOM)
        ged_path = f.name

    try:
        tree_data = load_tree(ged_path)
    finally:
        os.unlink(ged_path)

    print(f"\nImported {len(tree_data['individuals'])} individuals from GEDCOM")
    print(f"Relationships: {len(tree_data['relationships'])}")

    # Show individuals
    for ind in tree_data["individuals"]:
        born = f", born {ind['birth_date']}" if ind.get("birth_date") else ""
        place = f" in {ind['birth_place']}" if ind.get("birth_place") else ""
        print(f"  • {ind['name']}{born}{place}")

    return tree_data


# ---------------------------------------------------------------------------
# Example 2: Import from JSON
# ---------------------------------------------------------------------------

def example_json_import():
    print("\n" + "=" * 60)
    print("Example 2: Import from JSON")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(SAMPLE_JSON, f)
        json_path = f.name

    try:
        tree_data = load_tree(json_path)
    finally:
        os.unlink(json_path)

    print(f"\nImported {len(tree_data['individuals'])} individuals from JSON")
    parent_rels = [r for r in tree_data["relationships"] if r["type"] == "parent"]
    print(f"Parent relationships derived: {len(parent_rels)}")

    return tree_data


# ---------------------------------------------------------------------------
# Example 3: Build hierarchy and run discovery cycle (GEDCOM tree)
# ---------------------------------------------------------------------------

def example_discovery_cycle(tree_data):
    print("\n" + "=" * 60)
    print("Example 3: Build Agent Hierarchy & Run Discovery Cycle")
    print("=" * 60)

    manager = FamilyTreeManager(name="SchmidtFamilyTree")
    summary = manager.load_tree(tree_data)

    print(f"\nTree loaded:")
    print(f"  Total agents : {summary['total_nodes']}")
    print(f"  Scout agents : {summary['scout_nodes']}  (oldest known generation — no parents)")
    print(f"  Youngest gen : {summary['youngest_nodes']} (no children)")

    # Show scout details before discovery
    print("\nLineage scouts (will search for new relatives):")
    for scout in manager.get_scouts():
        print(f"  🔍 {scout.name}  [{scout.person_id}]")
        briefing = scout.distil_knowledge()
        print(f"     Summary: {briefing['summary'][:80]}...")

    # Run the discovery cycle
    print("\nRunning discovery cycle …")
    result = manager.run_discovery_cycle()

    print(f"\nDiscovery cycle complete:")
    print(f"  Scouts activated : {result['scouts_activated']}")
    print(f"  Total discoveries: {result['total_discoveries']}")

    for report in result["scout_reports"]:
        print(f"\n  Scout: {report['scout_name']}  [{report['scout_id']}]")
        print(f"    Clues used: {len(report['clues_used'])}")
        for clue in report["clues_used"][:4]:
            print(f"      - [{clue['type']}] {clue['value']}")
        if report["new_relatives_found"]:
            for rel in report["new_relatives_found"]:
                print(f"    → {rel['description'][:100]}")

    return manager


# ---------------------------------------------------------------------------
# Example 4: Inspect individual node agents
# ---------------------------------------------------------------------------

def example_inspect_nodes(manager):
    print("\n" + "=" * 60)
    print("Example 4: Inspect Individual Node Agents")
    print("=" * 60)

    for pid, node in manager.get_all_nodes().items():
        status = node.get_status()
        is_scout = isinstance(node, LineageScoutAgent)
        role = "🔍 Scout" if is_scout else "📄 Node "
        print(
            f"\n  {role}  {status['person_name']!r:30s}  "
            f"[{pid}]"
        )
        print(f"    Mother : {status['mother'] or '—'}")
        print(f"    Father : {status['father'] or '—'}")
        print(f"    Children  : {status['children'] or ['—']}")
        print(f"    Knowledge contributions : {status['knowledge_contributions']}")
        print(f"    Discovery reports       : {status['discovery_reports']}")


# ---------------------------------------------------------------------------
# Example 5: Full pipeline using the FamilyTreeManager.process() API
# ---------------------------------------------------------------------------

def example_process_api():
    print("\n" + "=" * 60)
    print("Example 5: FamilyTreeManager.process() API")
    print("=" * 60)

    manager = FamilyTreeManager(name="IrishTree")

    # Load via process()
    load_result = manager.process({
        "action": "load",
        "data": {
            "source": "json",
            "individuals": [
                {"id": "A1", "name": "Colm O'Brien", "birth_place": "Galway"},
                {"id": "B1", "name": "Patrick O'Brien", "birth_place": "Boston"},
                {"id": "C1", "name": "Sean O'Brien", "birth_place": "New York"},
            ],
            "relationships": [
                {"type": "parent", "parent": "A1", "child": "B1", "parent_role": "father"},
                {"type": "parent", "parent": "B1", "child": "C1", "parent_role": "father"},
            ],
        },
    })
    print(f"\nLoaded: {load_result}")

    # Get a specific node
    node_status = manager.process({"action": "get_node", "person_id": "C1"})
    print(f"\nYoungest node (C1):")
    print(f"  Name   : {node_status['person_name']}")
    print(f"  Father : {node_status['father']}")

    # Run discovery
    discovery = manager.process({"action": "run_discovery"})
    print(f"\nDiscovery: scouts={discovery['scouts_activated']}, "
          f"discoveries={discovery['total_discoveries']}")

    # Manager status
    status = manager.process({"action": "status"})
    print(f"\nManager status: {status}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gedcom_tree = example_gedcom_import()
    _json_tree = example_json_import()

    manager = example_discovery_cycle(gedcom_tree)
    example_inspect_nodes(manager)
    example_process_api()

    print("\n" + "=" * 60)
    print("All examples completed successfully.")
    print("=" * 60)
