"""Archivist agent for family tree parsing, merging, and relationship inference."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx
from sagascout.core.base_agent import BaseAgent


class Archivist(BaseAgent):
    """
    Archivist agent specializes in family tree operations.
    
    Capabilities:
    - Parse family tree data from various formats
    - Merge multiple family trees
    - Infer relationships between individuals
    - Detect conflicts and duplicates
    """

    def __init__(self, name: str = "Archivist", config: Dict[str, Any] = None):
        """
        Initialize Archivist agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary
        """
        super().__init__(name, config)
        self.tree = nx.DiGraph()
        self.individuals = {}

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process family tree data.

        Args:
            input_data: Dictionary containing tree operations
                - action: 'parse', 'merge', 'infer', or 'query'
                - data: Relevant data for the action

        Returns:
            Dictionary with processing results
        """
        action = input_data.get("action")
        data = input_data.get("data", {})

        result = {}

        if action == "parse":
            result = self.parse_tree(data)
        elif action == "merge":
            result = self.merge_trees(data)
        elif action == "infer":
            result = self.infer_relationship(
                data.get("person1"), data.get("person2")
            )
        elif action == "query":
            result = self.query_tree(data)
        elif action == "parse_gedcom":
            result = self.parse_gedcom(data.get("filepath", ""))
        elif action == "export_gedcom":
            result = self.export_gedcom(data.get("filepath", ""))
        elif action == "to_json":
            result = self.to_json()
        else:
            result = {"error": f"Unknown action: {action}"}

        # Remember this operation
        self.remember({
            "event": "tree_operation",
            "action": action,
            "nodes": self.tree.number_of_nodes(),
            "edges": self.tree.number_of_edges(),
        })

        return result

    def parse_tree(self, tree_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse family tree from input data.

        Args:
            tree_data: Dictionary containing individuals and relationships

        Returns:
            Parsing results
        """
        individuals = tree_data.get("individuals", [])
        relationships = tree_data.get("relationships", [])

        # Add individuals to tree
        for person in individuals:
            person_id = person.get("id")
            self.individuals[person_id] = person
            self.tree.add_node(person_id, **person)

        # Add relationships
        for rel in relationships:
            parent_id = rel.get("parent")
            child_id = rel.get("child")
            rel_type = rel.get("type", "parent")
            
            if parent_id and child_id:
                self.tree.add_edge(parent_id, child_id, relationship=rel_type)

        return {
            "status": "success",
            "individuals_added": len(individuals),
            "relationships_added": len(relationships),
            "total_nodes": self.tree.number_of_nodes(),
            "total_edges": self.tree.number_of_edges(),
        }

    def merge_trees(self, merge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge another family tree into the current tree.

        Args:
            merge_data: Data from another tree to merge

        Returns:
            Merge results including conflicts detected
        """
        other_individuals = merge_data.get("individuals", [])
        other_relationships = merge_data.get("relationships", [])
        
        conflicts = []
        merged_count = 0
        new_count = 0

        # Merge individuals
        for person in other_individuals:
            person_id = person.get("id")
            
            if person_id in self.individuals:
                # Check for conflicts
                existing = self.individuals[person_id]
                conflict = self._detect_conflicts(existing, person)
                if conflict:
                    conflicts.append(conflict)
                else:
                    # Merge data
                    self.individuals[person_id].update(person)
                    merged_count += 1
            else:
                # Add new individual
                self.individuals[person_id] = person
                self.tree.add_node(person_id, **person)
                new_count += 1

        # Merge relationships
        for rel in other_relationships:
            parent_id = rel.get("parent")
            child_id = rel.get("child")
            
            if parent_id and child_id:
                if not self.tree.has_edge(parent_id, child_id):
                    self.tree.add_edge(
                        parent_id, child_id, relationship=rel.get("type", "parent")
                    )

        return {
            "status": "success",
            "merged_individuals": merged_count,
            "new_individuals": new_count,
            "conflicts": conflicts,
            "total_nodes": self.tree.number_of_nodes(),
            "total_edges": self.tree.number_of_edges(),
        }

    def infer_relationship(
        self, person1_id: str, person2_id: str
    ) -> Dict[str, Any]:
        """
        Infer relationship between two individuals.

        Args:
            person1_id: First person's ID
            person2_id: Second person's ID

        Returns:
            Inferred relationship information
        """
        if person1_id not in self.tree or person2_id not in self.tree:
            return {"error": "One or both individuals not found in tree"}

        try:
            # Find shortest path
            path = nx.shortest_path(
                self.tree.to_undirected(), person1_id, person2_id
            )
            
            # Analyze path to determine relationship
            relationship = self._analyze_path(path)
            
            return {
                "person1": person1_id,
                "person2": person2_id,
                "relationship": relationship,
                "path": path,
                "path_length": len(path) - 1,
            }
        except nx.NetworkXNoPath:
            return {
                "person1": person1_id,
                "person2": person2_id,
                "relationship": "No direct relationship found",
                "path": [],
            }

    def query_tree(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query the family tree.

        Args:
            query: Query parameters

        Returns:
            Query results
        """
        query_type = query.get("type")
        person_id = query.get("person_id")

        if query_type == "ancestors":
            return self._get_ancestors(person_id)
        elif query_type == "descendants":
            return self._get_descendants(person_id)
        elif query_type == "siblings":
            return self._get_siblings(person_id)
        elif query_type == "statistics":
            return self._get_statistics()
        else:
            return {"error": f"Unknown query type: {query_type}"}

    def _validate_person_exists(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate that a person exists in the tree.

        Args:
            person_id: Person's ID

        Returns:
            Error dictionary if person not found, None otherwise
        """
        if person_id not in self.tree:
            return {"error": "Person not found"}
        return None

    def _get_ancestors(self, person_id: str) -> Dict[str, Any]:
        """Get all ancestors of a person."""
        error = self._validate_person_exists(person_id)
        if error:
            return error

        ancestors = list(nx.ancestors(self.tree, person_id))
        return {
            "person_id": person_id,
            "ancestors": ancestors,
            "count": len(ancestors),
        }

    def _get_descendants(self, person_id: str) -> Dict[str, Any]:
        """Get all descendants of a person."""
        error = self._validate_person_exists(person_id)
        if error:
            return error

        descendants = list(nx.descendants(self.tree, person_id))
        return {
            "person_id": person_id,
            "descendants": descendants,
            "count": len(descendants),
        }

    def _get_siblings(self, person_id: str) -> Dict[str, Any]:
        """Get siblings of a person."""
        error = self._validate_person_exists(person_id)
        if error:
            return error

        # Find parents
        parents = list(self.tree.predecessors(person_id))
        siblings = []

        for parent in parents:
            # Get all children of this parent
            children = list(self.tree.successors(parent))
            siblings.extend([c for c in children if c != person_id])

        # Remove duplicates
        siblings = list(set(siblings))

        return {
            "person_id": person_id,
            "siblings": siblings,
            "count": len(siblings),
        }

    def _get_statistics(self) -> Dict[str, Any]:
        """Get tree statistics."""
        return {
            "total_individuals": self.tree.number_of_nodes(),
            "total_relationships": self.tree.number_of_edges(),
            "generations": self._calculate_generations(),
        }

    def _calculate_generations(self) -> int:
        """Calculate the number of generations in the tree."""
        if self.tree.number_of_nodes() == 0:
            return 0

        # Find root nodes (nodes with no predecessors)
        roots = [n for n in self.tree.nodes() if self.tree.in_degree(n) == 0]
        
        if not roots:
            return 0

        max_depth = 0
        for root in roots:
            depths = nx.single_source_shortest_path_length(self.tree, root)
            max_depth = max(max_depth, max(depths.values()) if depths else 0)

        return max_depth + 1

    def _analyze_path(self, path: List[str]) -> str:
        """Analyze a path to determine relationship."""
        if len(path) == 1:
            return "Same person"
        elif len(path) == 2:
            # Direct relationship
            if self.tree.has_edge(path[0], path[1]):
                return "Parent/Child"
            else:
                return "Child/Parent"
        elif len(path) == 3:
            return "Sibling or Grandparent/Grandchild"
        else:
            # Calculate cousin relationship
            generations = len(path) - 1
            return f"{generations}th degree relative"

    def _detect_conflicts(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Detect conflicts between two person records."""
        conflicts = {}
        
        for key in ["birth_date", "death_date", "name"]:
            if key in existing and key in new:
                if existing[key] != new[key]:
                    conflicts[key] = {
                        "existing": existing[key],
                        "new": new[key],
                    }

        if conflicts:
            return {
                "person_id": existing.get("id"),
                "conflicts": conflicts,
            }

        return None

    # ------------------------------------------------------------------ #
    # GEDCOM support                                                       #
    # ------------------------------------------------------------------ #

    def parse_gedcom(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a GEDCOM (.ged) file and load individuals and relationships.

        Requires ``python-gedcom`` (``pip install python-gedcom``).

        Args:
            filepath: Path to the GEDCOM file

        Returns:
            Dictionary with parsing results
        """
        try:
            from gedcom.parser import Parser
            from gedcom.element.individual import IndividualElement
            from gedcom.element.family import FamilyElement
        except ImportError:
            return {"error": "python-gedcom is not installed. Run: pip install python-gedcom"}

        path = Path(filepath)
        if not path.is_file():
            return {"error": f"File not found: {filepath}"}

        parser = Parser()
        parser.parse_file(str(path))

        individuals_added = 0
        relationships_added = 0
        root_child_elements = parser.get_root_child_elements()

        # Index individuals first
        id_map: Dict[str, str] = {}  # gedcom pointer -> our id
        for element in root_child_elements:
            if isinstance(element, IndividualElement):
                pointer = element.get_pointer()
                # Use pointer as ID (strip @)
                person_id = pointer.strip("@")
                (first, last) = element.get_name()
                name = f"{first} {last}".strip() or person_id
                birth_data = element.get_birth_data()
                death_data = element.get_death_data()
                person = {
                    "id": person_id,
                    "name": name,
                }
                if birth_data:
                    person["birth_date"] = birth_data[0] or None
                    person["birth_place"] = birth_data[1] or None
                if death_data:
                    person["death_date"] = death_data[0] or None
                self.individuals[person_id] = person
                self.tree.add_node(person_id, **person)
                id_map[pointer] = person_id
                individuals_added += 1

        # Process family relationships
        for element in root_child_elements:
            if isinstance(element, FamilyElement):
                children_ids = []
                for child_element in element.get_child_elements():
                    tag = child_element.get_tag()
                    ptr = child_element.get_value()
                    if tag == "CHIL":
                        children_ids.append(id_map.get(ptr))
                    elif tag in ("HUSB", "WIFE"):
                        # Will be used as parent(s)
                        pass

                # Build parent list for this family
                parent_ids = []
                for child_element in element.get_child_elements():
                    tag = child_element.get_tag()
                    ptr = child_element.get_value()
                    if tag in ("HUSB", "WIFE"):
                        pid = id_map.get(ptr)
                        if pid:
                            parent_ids.append(pid)

                for parent_id in parent_ids:
                    for child_id in children_ids:
                        if child_id and not self.tree.has_edge(parent_id, child_id):
                            self.tree.add_edge(parent_id, child_id, relationship="parent")
                            relationships_added += 1

        return {
            "status": "success",
            "individuals_added": individuals_added,
            "relationships_added": relationships_added,
            "total_nodes": self.tree.number_of_nodes(),
            "total_edges": self.tree.number_of_edges(),
        }

    def export_gedcom(self, filepath: str) -> Dict[str, Any]:
        """
        Export the current family tree as a GEDCOM (.ged) file.

        Produces a minimal but standards-compliant GEDCOM 5.5.1 file.

        Args:
            filepath: Destination file path

        Returns:
            Dictionary with export results
        """
        lines = ["0 HEAD", "1 GEDC", "2 VERS 5.5.1", "2 FORM LINEAGE-LINKED",
                 "1 CHAR UTF-8"]

        for person_id, person in self.individuals.items():
            pointer = f"@{person_id}@"
            lines.append(f"0 {pointer} INDI")
            name = person.get("name", "")
            if name:
                lines.append(f"1 NAME {name}")
            birth_date = person.get("birth_date")
            birth_place = person.get("birth_place")
            if birth_date or birth_place:
                lines.append("1 BIRT")
                if birth_date:
                    lines.append(f"2 DATE {birth_date}")
                if birth_place:
                    lines.append(f"2 PLAC {birth_place}")
            death_date = person.get("death_date")
            if death_date:
                lines.append("1 DEAT")
                lines.append(f"2 DATE {death_date}")

        # Write family records grouped by parent->child edges
        written_families: set = set()
        fam_counter = 0
        for parent_id in self.tree.nodes():
            children = list(self.tree.successors(parent_id))
            if not children:
                continue
            fam_key = (parent_id, tuple(sorted(children)))
            if fam_key in written_families:
                continue
            written_families.add(fam_key)
            fam_id = f"@F{fam_counter}@"
            fam_counter += 1
            lines.append(f"0 {fam_id} FAM")
            lines.append(f"1 HUSB @{parent_id}@")
            for child_id in children:
                lines.append(f"1 CHIL @{child_id}@")

        lines.append("0 TRLR")

        Path(filepath).write_text("\n".join(lines), encoding="utf-8")

        return {
            "status": "success",
            "filepath": filepath,
            "individuals_exported": len(self.individuals),
        }

    # ------------------------------------------------------------------ #
    # JSON serialization                                                   #
    # ------------------------------------------------------------------ #

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the current tree state to a JSON-compatible dictionary.

        Returns:
            Dictionary containing individuals and adjacency list
        """
        adjacency = [
            {"parent": u, "child": v, "type": data.get("relationship", "parent")}
            for u, v, data in self.tree.edges(data=True)
        ]
        return {
            "individuals": list(self.individuals.values()),
            "relationships": adjacency,
        }

    def save_to_file(self, filepath: str) -> None:
        """
        Save tree state to a JSON file.

        Args:
            filepath: Destination file path
        """
        Path(filepath).write_text(
            json.dumps(self.to_json(), indent=2), encoding="utf-8"
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any], name: str = "Archivist",
                  config: Dict[str, Any] = None) -> "Archivist":
        """
        Restore an Archivist from a previously serialized dictionary.

        Args:
            data: Dictionary as returned by :meth:`to_json`
            name: Agent name
            config: Optional configuration

        Returns:
            Archivist instance populated with the saved state
        """
        archivist = cls(name=name, config=config)
        archivist.parse_tree(data)
        return archivist

    @classmethod
    def load_from_file(cls, filepath: str, name: str = "Archivist",
                       config: Dict[str, Any] = None) -> "Archivist":
        """
        Load an Archivist from a JSON file saved by :meth:`save_to_file`.

        Args:
            filepath: Source file path
            name: Agent name
            config: Optional configuration

        Returns:
            Archivist instance populated with the saved state
        """
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        return cls.from_json(data, name=name, config=config)
