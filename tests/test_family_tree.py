"""Tests for the family tree agent system and importers."""

import json
import os
import tempfile

import pytest

from sagascout import FamilyTreeManager, FamilyNodeAgent, LineageScoutAgent
from sagascout.utils import GEDCOMImporter, JSONImporter, load_tree


# ---------------------------------------------------------------------------
# Fixtures and sample data
# ---------------------------------------------------------------------------

SAMPLE_GEDCOM = """\
0 HEAD
1 SOUR SagaScout
0 @I1@ INDI
1 NAME George /Smith/
1 SEX M
1 BIRT
2 DATE 1 JAN 1880
2 PLAC London, England
1 OCCU Blacksmith
0 @I2@ INDI
1 NAME Mary /Jones/
1 SEX F
1 BIRT
2 DATE 15 MAR 1885
2 PLAC Bristol, England
0 @I3@ INDI
1 NAME John /Smith/
1 SEX M
1 BIRT
2 DATE 10 JUN 1910
2 PLAC Manchester, England
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 MARR
2 DATE 20 APR 1905
2 PLAC London, England
0 @I4@ INDI
1 NAME Alice /Smith/
1 SEX F
1 BIRT
2 DATE 5 SEP 1940
2 PLAC Manchester, England
0 @F2@ FAM
1 HUSB @I3@
1 CHIL @I4@
0 TRLR
"""

SAMPLE_JSON_FLAT = json.dumps([
    {"id": "p1", "name": "Robert Brown", "sex": "M", "birth_date": "1870", "birth_place": "Dublin"},
    {"id": "p2", "name": "Susan Green", "sex": "F", "birth_date": "1875", "birth_place": "Cork"},
    {"id": "p3", "name": "William Brown", "sex": "M", "birth_date": "1900",
     "birth_place": "Dublin", "father_id": "p1", "mother_id": "p2"},
    {"id": "p4", "name": "Emma Brown", "sex": "F", "birth_date": "1930",
     "birth_place": "London", "father_id": "p3"},
])

SAMPLE_JSON_NATIVE = json.dumps({
    "individuals": [
        {"id": "n1", "name": "Ancestor One", "birth_date": "1800", "birth_place": "Paris"},
        {"id": "n2", "name": "Child One", "birth_date": "1830", "birth_place": "Lyon"},
    ],
    "relationships": [
        {"type": "parent", "parent": "n1", "child": "n2", "parent_role": "father"},
    ],
})


# ---------------------------------------------------------------------------
# GEDCOMImporter tests
# ---------------------------------------------------------------------------

class TestGEDCOMImporter:
    def test_parse_string_returns_individuals(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        assert "individuals" in result
        assert len(result["individuals"]) == 4

    def test_parse_string_returns_relationships(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        parent_rels = [r for r in result["relationships"] if r["type"] == "parent"]
        # F1: George→John, Mary→John; F2: John→Alice
        assert len(parent_rels) == 3

    def test_parse_names_cleaned(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        names = {ind["name"] for ind in result["individuals"]}
        assert "George Smith" in names
        assert "Mary Jones" in names

    def test_parse_birth_date_and_place(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        george = next(i for i in result["individuals"] if i["name"] == "George Smith")
        assert george["birth_date"] == "1 JAN 1880"
        assert george["birth_place"] == "London, England"

    def test_spouse_relationship_present(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        spouse_rels = [r for r in result["relationships"] if r["type"] == "spouse"]
        assert len(spouse_rels) == 1

    def test_source_tag(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        assert result["source"] == "gedcom"

    def test_parse_file(self, tmp_path):
        ged_file = tmp_path / "test.ged"
        ged_file.write_text(SAMPLE_GEDCOM, encoding="utf-8")
        result = GEDCOMImporter().parse_file(str(ged_file))
        assert len(result["individuals"]) == 4

    def test_occupation_parsed(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        george = next(i for i in result["individuals"] if i["name"] == "George Smith")
        assert george["occupation"] == "Blacksmith"

    def test_father_role_in_relationships(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        george_child = [
            r for r in result["relationships"]
            if r["type"] == "parent" and r["parent"] == "I1"
        ]
        assert george_child[0]["parent_role"] == "father"

    def test_mother_role_in_relationships(self):
        result = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        mary_child = [
            r for r in result["relationships"]
            if r["type"] == "parent" and r["parent"] == "I2"
        ]
        assert mary_child[0]["parent_role"] == "mother"


# ---------------------------------------------------------------------------
# JSONImporter tests
# ---------------------------------------------------------------------------

class TestJSONImporter:
    def test_flat_list_returns_individuals(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        assert len(result["individuals"]) == 4

    def test_flat_list_derives_relationships(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        parent_rels = [r for r in result["relationships"] if r["type"] == "parent"]
        # p3 has father p1 and mother p2; p4 has father p3 → 3 relationships
        assert len(parent_rels) == 3

    def test_native_format_passthrough(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_NATIVE)
        assert len(result["individuals"]) == 2
        assert len(result["relationships"]) == 1

    def test_source_tag(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        assert result["source"] == "json"

    def test_parse_file(self, tmp_path):
        json_file = tmp_path / "tree.json"
        json_file.write_text(SAMPLE_JSON_FLAT, encoding="utf-8")
        result = JSONImporter().parse_file(str(json_file))
        assert len(result["individuals"]) == 4

    def test_name_preserved(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        names = {i["name"] for i in result["individuals"]}
        assert "Robert Brown" in names

    def test_birth_place_preserved(self):
        result = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        robert = next(i for i in result["individuals"] if i["name"] == "Robert Brown")
        assert robert["birth_place"] == "Dublin"

    def test_bare_list_input(self):
        data = [{"id": "x1", "name": "Solo Person"}]
        result = JSONImporter().parse_dict(data)
        assert len(result["individuals"]) == 1


# ---------------------------------------------------------------------------
# load_tree convenience function
# ---------------------------------------------------------------------------

class TestLoadTree:
    def test_ged_extension_routes_to_gedcom(self, tmp_path):
        ged_file = tmp_path / "family.ged"
        ged_file.write_text(SAMPLE_GEDCOM, encoding="utf-8")
        result = load_tree(str(ged_file))
        assert result["source"] == "gedcom"

    def test_json_extension_routes_to_json(self, tmp_path):
        json_file = tmp_path / "family.json"
        json_file.write_text(SAMPLE_JSON_FLAT, encoding="utf-8")
        result = load_tree(str(json_file))
        assert result["source"] == "json"

    def test_unknown_extension_raises(self, tmp_path):
        csv_file = tmp_path / "family.csv"
        csv_file.write_text("id,name\n1,Test", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_tree(str(csv_file))


# ---------------------------------------------------------------------------
# FamilyNodeAgent tests
# ---------------------------------------------------------------------------

class TestFamilyNodeAgent:
    def _make_node(self, pid="p1", name="Test Person"):
        return FamilyNodeAgent(pid, {"id": pid, "name": name, "birth_place": "Rome"})

    def test_initial_state(self):
        node = self._make_node()
        assert node.person_id == "p1"
        assert node.mother_agent is None
        assert node.father_agent is None
        assert node.child_agents == []

    def test_set_mother_links_both_ways(self):
        child = self._make_node("c1", "Child")
        mother = self._make_node("m1", "Mother")
        child.set_mother(mother)
        assert child.mother_agent is mother
        assert child in mother.child_agents

    def test_set_father_links_both_ways(self):
        child = self._make_node("c1", "Child")
        father = self._make_node("f1", "Father")
        child.set_father(father)
        assert child.father_agent is father
        assert child in father.child_agents

    def test_distil_knowledge_includes_person_data(self):
        node = self._make_node("p1", "Alice")
        briefing = node.distil_knowledge()
        assert briefing["person_id"] == "p1"
        assert briefing["name"] == "Alice"
        assert "Rome" in briefing["summary"]

    def test_contribute_knowledge_to_parents_reaches_parent(self):
        child = self._make_node("c1", "Child")
        parent = self._make_node("p1", "Parent")
        child.set_father(parent)
        child.contribute_knowledge_to_parents()
        assert len(parent._collected_knowledge) == 1

    def test_accept_knowledge_increments_count(self):
        node = self._make_node()
        result = node.process({
            "action": "contribute_knowledge",
            "knowledge": {"person_id": "x", "summary": "test"},
        })
        assert result["total_contributions"] == 1

    def test_get_status_returns_expected_keys(self):
        node = self._make_node()
        status = node.get_status()
        assert "person_id" in status
        assert "children" in status
        assert "knowledge_contributions" in status

    def test_relay_report_stores_report(self):
        node = self._make_node()
        node.process({"action": "relay_report", "report": {"scout_id": "s1"}})
        assert len(node._discovery_reports) == 1


# ---------------------------------------------------------------------------
# LineageScoutAgent tests
# ---------------------------------------------------------------------------

class TestLineageScoutAgent:
    def _make_scout(self, pid="s1", name="Ancient Ancestor"):
        return LineageScoutAgent(
            pid,
            {"id": pid, "name": name, "birth_place": "Athens", "notes": ["Emigrated ca. 1800"]},
        )

    def test_is_family_node_agent(self):
        scout = self._make_scout()
        assert isinstance(scout, FamilyNodeAgent)

    def test_run_discovery_returns_report(self):
        scout = self._make_scout()
        report = scout.run_discovery()
        assert report["scout_id"] == "s1"
        assert "clues_used" in report
        assert "new_relatives_found" in report
        assert report["status"] == "completed"

    def test_clues_include_own_location(self):
        scout = self._make_scout()
        clues = scout._derive_clues()
        locations = [c["value"] for c in clues if c["type"] == "location"]
        assert "Athens" in locations

    def test_clues_include_own_surname(self):
        scout = self._make_scout(name="John Papadopoulos")
        clues = scout._derive_clues()
        surnames = [c["value"] for c in clues if c["type"] == "surname"]
        assert "Papadopoulos" in surnames

    def test_clues_deduplicated(self):
        scout = self._make_scout()
        # Add duplicate location via a descendant contribution
        scout._collected_knowledge.append({
            "person_id": "child1", "birth_place": "Athens", "name": None, "notes": []
        })
        clues = scout._derive_clues()
        locations = [c["value"] for c in clues if c["type"] == "location"]
        assert locations.count("Athens") == 1

    def test_discovery_relayed_to_children(self):
        scout = self._make_scout()
        child = FamilyNodeAgent("c1", {"id": "c1", "name": "Child"})
        scout.add_child(child)
        scout.run_discovery()
        assert len(child._discovery_reports) == 1

    def test_notes_included_as_clues(self):
        scout = self._make_scout()
        clues = scout._derive_clues()
        note_clues = [c for c in clues if c["type"] == "note"]
        assert any("Emigrated" in c["value"] for c in note_clues)


# ---------------------------------------------------------------------------
# FamilyTreeManager tests
# ---------------------------------------------------------------------------

class TestFamilyTreeManager:
    def _make_simple_tree_data(self):
        """Three-generation tree: grandparent → parent → child."""
        return {
            "source": "json",
            "individuals": [
                {"id": "gp1", "name": "Grand Pa", "birth_place": "Berlin", "sex": "M"},
                {"id": "gm1", "name": "Grand Ma", "birth_place": "Hamburg", "sex": "F"},
                {"id": "dad", "name": "Dad Smith", "birth_place": "Munich", "sex": "M"},
                {"id": "kid", "name": "Kid Smith", "birth_place": "Vienna", "sex": "M"},
            ],
            "relationships": [
                {"type": "parent", "parent": "gp1", "child": "dad", "parent_role": "father"},
                {"type": "parent", "parent": "gm1", "child": "dad", "parent_role": "mother"},
                {"type": "parent", "parent": "dad", "child": "kid", "parent_role": "father"},
            ],
        }

    def test_load_tree_returns_summary(self):
        manager = FamilyTreeManager()
        result = manager.load_tree(self._make_simple_tree_data())
        assert result["status"] == "loaded"
        assert result["total_nodes"] == 4

    def test_scouts_created_for_root_nodes(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        scouts = manager.get_scouts()
        # gp1 and gm1 have no parents → 2 scouts
        assert len(scouts) == 2

    def test_scout_nodes_are_lineage_scout_agents(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        for scout in manager.get_scouts():
            assert isinstance(scout, LineageScoutAgent)

    def test_run_discovery_cycle_returns_report(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        result = manager.run_discovery_cycle()
        assert result["status"] == "completed"
        assert result["scouts_activated"] == 2
        assert "scout_reports" in result

    def test_knowledge_propagated_to_scouts(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        manager._propagate_knowledge()
        for scout in manager.get_scouts():
            # Each grandparent scout should have received knowledge from dad
            assert len(scout._collected_knowledge) >= 1

    def test_process_load_action(self):
        manager = FamilyTreeManager()
        result = manager.process({
            "action": "load",
            "data": self._make_simple_tree_data(),
        })
        assert result["status"] == "loaded"

    def test_process_run_discovery_action(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        result = manager.process({"action": "run_discovery"})
        assert result["status"] == "completed"

    def test_process_get_node_action(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        result = manager.process({"action": "get_node", "person_id": "kid"})
        assert result["person_id"] == "kid"

    def test_process_get_node_unknown(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        result = manager.process({"action": "get_node", "person_id": "nobody"})
        assert "error" in result

    def test_empty_tree_discovery_returns_error(self):
        manager = FamilyTreeManager()
        result = manager.run_discovery_cycle()
        assert "error" in result

    def test_get_status_keys(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        status = manager.get_status()
        assert "total_nodes" in status
        assert "scout_nodes" in status
        assert "discovery_cycles_run" in status

    def test_load_from_gedcom_string(self):
        tree_data = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        manager = FamilyTreeManager()
        result = manager.load_tree(tree_data)
        assert result["total_nodes"] == 4

    def test_load_from_json_string(self):
        tree_data = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        manager = FamilyTreeManager()
        result = manager.load_tree(tree_data)
        assert result["total_nodes"] == 4

    def test_full_cycle_gedcom(self):
        tree_data = GEDCOMImporter().parse_string(SAMPLE_GEDCOM)
        manager = FamilyTreeManager()
        manager.load_tree(tree_data)
        result = manager.run_discovery_cycle()
        assert result["status"] == "completed"
        assert result["scouts_activated"] > 0

    def test_full_cycle_json(self):
        tree_data = JSONImporter().parse_string(SAMPLE_JSON_FLAT)
        manager = FamilyTreeManager()
        manager.load_tree(tree_data)
        result = manager.run_discovery_cycle()
        assert result["status"] == "completed"

    def test_discovery_reports_stored_on_manager(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        manager.run_discovery_cycle()
        assert len(manager._discovery_reports) > 0

    def test_child_nodes_receive_relay(self):
        manager = FamilyTreeManager()
        manager.load_tree(self._make_simple_tree_data())
        manager.run_discovery_cycle()
        # The youngest node ("kid") should have received relayed reports
        kid_node = manager.get_node("kid")
        assert len(kid_node._discovery_reports) > 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
