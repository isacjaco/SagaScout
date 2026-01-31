"""Archivist agent for family tree parsing, merging, and relationship inference."""

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

    def _get_ancestors(self, person_id: str) -> Dict[str, Any]:
        """Get all ancestors of a person."""
        if person_id not in self.tree:
            return {"error": "Person not found"}

        ancestors = list(nx.ancestors(self.tree, person_id))
        return {
            "person_id": person_id,
            "ancestors": ancestors,
            "count": len(ancestors),
        }

    def _get_descendants(self, person_id: str) -> Dict[str, Any]:
        """Get all descendants of a person."""
        if person_id not in self.tree:
            return {"error": "Person not found"}

        descendants = list(nx.descendants(self.tree, person_id))
        return {
            "person_id": person_id,
            "descendants": descendants,
            "count": len(descendants),
        }

    def _get_siblings(self, person_id: str) -> Dict[str, Any]:
        """Get siblings of a person."""
        if person_id not in self.tree:
            return {"error": "Person not found"}

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
