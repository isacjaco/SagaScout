"""
Hierarchical family-tree agent system for SagaScout.

Architecture
------------
Each person in the family tree is represented by a **FamilyNodeAgent**.
Leaf nodes (individuals with no known parents, i.e. the oldest known
generation in any lineage) are promoted to **LineageScoutAgent** instances,
which actively search for new relatives.

Knowledge flows in two directions:

1. **Downward (descendants → ancestors):**
   Each generation distils its collective knowledge — DNA clues, research
   leads, document evidence — into a *briefing* that is passed up to its
   parents.  The LineageScoutAgent at the top of each lineage receives the
   fully-accumulated briefing and uses it to drive discovery.

2. **Upward (ancestors → descendants / tree manager):**
   Scouts report their discoveries back through the chain.  Each node
   relays the report to its own parent until it reaches the
   **FamilyTreeManager**, which aggregates everything.

Usage
-----
::

    from sagascout.agents.family_tree import FamilyTreeManager
    from sagascout.utils.importers import load_tree

    tree_data = load_tree("family.ged")
    manager = FamilyTreeManager(name="MyTree")
    manager.load_tree(tree_data)
    report = manager.run_discovery_cycle()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import networkx as nx

from sagascout.core.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# FamilyNodeAgent
# ---------------------------------------------------------------------------


class FamilyNodeAgent(BaseAgent):
    """
    Agent representing one person (node) in the family tree.

    Each node knows:
    - Its own biographical data.
    - Its direct parent agents (mother / father).
    - Its direct child agents.
    - The collective knowledge distilled from all descendant nodes.

    Relationships between nodes mirror the genealogical relationships: the
    *youngest* known generation sits at the bottom of the tree;
    *oldest* (earliest ancestors) sit at the top.

    The node can:
    - Accept knowledge contributions from its children.
    - Distil those contributions into a compact briefing.
    - Forward the briefing to its own parents (upward propagation toward
      the scout at the top of the lineage).
    - Receive discovery reports from parent scouts and relay them downward
      to the tree manager.
    """

    def __init__(
        self,
        person_id: str,
        person_data: Dict[str, Any],
        name: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        agent_name = name or f"Node-{person_id}"
        super().__init__(agent_name, config)
        self.person_id = person_id
        self.person_data: Dict[str, Any] = dict(person_data)

        # Tree structure
        self.mother_agent: Optional[FamilyNodeAgent] = None
        self.father_agent: Optional[FamilyNodeAgent] = None
        self.child_agents: List[FamilyNodeAgent] = []

        # Knowledge containers
        self._collected_knowledge: List[Dict[str, Any]] = []
        self._discovery_reports: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Tree structure helpers
    # ------------------------------------------------------------------

    def add_child(self, child: FamilyNodeAgent) -> None:
        """Register *child* as a descendant of this node."""
        if child not in self.child_agents:
            self.child_agents.append(child)

    def set_mother(self, mother: FamilyNodeAgent) -> None:
        """Set the mother (parent) agent for this node."""
        self.mother_agent = mother
        mother.add_child(self)

    def set_father(self, father: FamilyNodeAgent) -> None:
        """Set the father (parent) agent for this node."""
        self.father_agent = father
        father.add_child(self)

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch an action on this node.

        Supported actions:
        - ``contribute_knowledge`` — a descendant is contributing knowledge.
        - ``distil`` — compute and return this node's distilled briefing.
        - ``relay_report`` — forward a discovery report from a scout.
        - ``status`` — return current node status.
        """
        action = input_data.get("action", "status")

        if action == "contribute_knowledge":
            return self._accept_knowledge(input_data.get("knowledge", {}))
        if action == "distil":
            return self.distil_knowledge()
        if action == "relay_report":
            return self._relay_report(input_data.get("report", {}))
        return self.get_status()

    # ------------------------------------------------------------------
    # Knowledge propagation — downward (descendants → ancestors)
    # ------------------------------------------------------------------

    def contribute_knowledge_to_parents(self) -> None:
        """
        Push this node's distilled knowledge to its parent agents.

        Called after all descendants have already contributed to this node
        so that the briefing is as complete as possible before forwarding.
        """
        briefing = self.distil_knowledge()
        if self.mother_agent:
            self.mother_agent.process({
                "action": "contribute_knowledge",
                "knowledge": briefing,
                "from_child": self.person_id,
            })
        if self.father_agent:
            self.father_agent.process({
                "action": "contribute_knowledge",
                "knowledge": briefing,
                "from_child": self.person_id,
            })

    def distil_knowledge(self) -> Dict[str, Any]:
        """
        Distil the node's own data plus all collected child knowledge into a
        compact briefing suitable for passing to ancestor agents / scouts.

        Returns:
            A dict containing the person's key biographical facts and a
            summary of all knowledge received from descendants.
        """
        person = self.person_data
        child_summaries = [k.get("summary", "") for k in self._collected_knowledge]

        summary_parts: List[str] = []
        if person.get("name"):
            summary_parts.append(f"Individual: {person['name']}")
        if person.get("birth_date") or person.get("birth_place"):
            born = " ".join(filter(None, [
                person.get("birth_date"), person.get("birth_place")
            ]))
            summary_parts.append(f"Born: {born}")
        if person.get("death_date") or person.get("death_place"):
            died = " ".join(filter(None, [
                person.get("death_date"), person.get("death_place")
            ]))
            summary_parts.append(f"Died: {died}")
        if person.get("occupation"):
            summary_parts.append(f"Occupation: {person['occupation']}")
        if child_summaries:
            summary_parts.append(
                f"Descendant clues ({len(child_summaries)}): "
                + "; ".join(cs for cs in child_summaries if cs)
            )

        briefing = {
            "person_id": self.person_id,
            "name": person.get("name"),
            "birth_date": person.get("birth_date"),
            "birth_place": person.get("birth_place"),
            "death_date": person.get("death_date"),
            "death_place": person.get("death_place"),
            "occupation": person.get("occupation"),
            "notes": person.get("notes", []),
            "sex": person.get("sex"),
            "descendant_knowledge": list(self._collected_knowledge),
            "summary": " | ".join(summary_parts),
        }

        self.remember({"event": "distil", "briefing_for": self.person_id})
        return briefing

    # ------------------------------------------------------------------
    # Knowledge propagation — upward (scouts → tree manager)
    # ------------------------------------------------------------------

    def relay_discovery_report(self, report: Dict[str, Any]) -> None:
        """
        Relay a scout's discovery report downward toward the tree manager.

        Each intermediate node stores the report and passes it on to its
        children, ultimately reaching the root (tree manager).
        """
        self._discovery_reports.append(report)
        for child in self.child_agents:
            child.process({"action": "relay_report", "report": report})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _accept_knowledge(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Accept a knowledge contribution from a descendant node."""
        self._collected_knowledge.append(knowledge)
        self.remember({
            "event": "knowledge_received",
            "from": knowledge.get("person_id"),
            "summary": knowledge.get("summary"),
        })
        return {"status": "accepted", "total_contributions": len(self._collected_knowledge)}

    def _relay_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Store and propagate a discovery report received from a parent scout."""
        self._discovery_reports.append(report)
        self.remember({"event": "report_received", "report_id": report.get("scout_id")})
        # Propagate further down the chain
        for child in self.child_agents:
            child.process({"action": "relay_report", "report": report})
        return {"status": "relayed"}

    # ------------------------------------------------------------------
    # Status / introspection
    # ------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        base = super().get_status()
        base.update({
            "person_id": self.person_id,
            "person_name": self.person_data.get("name"),
            "mother": self.mother_agent.person_id if self.mother_agent else None,
            "father": self.father_agent.person_id if self.father_agent else None,
            "children": [c.person_id for c in self.child_agents],
            "knowledge_contributions": len(self._collected_knowledge),
            "discovery_reports": len(self._discovery_reports),
        })
        return base


# ---------------------------------------------------------------------------
# LineageScoutAgent
# ---------------------------------------------------------------------------


class LineageScoutAgent(FamilyNodeAgent):
    """
    Scout agent placed at the *oldest known* position of each lineage.

    A LineageScoutAgent is a FamilyNodeAgent that has no known parents in the
    tree (i.e. it is a leaf node in the ancestor direction).  After receiving
    fully-distilled knowledge from all its descendants, it:

    1. Analyses the accumulated briefing to derive search targets.
    2. Simulates (or delegates to Oracle/Scout agents) discovery of new
       relatives.
    3. Reports findings back down through the chain to the tree manager.

    In a production system the ``_search_for_relatives`` method would
    dispatch real queries to Oracle, DNA Scout, or archive APIs.  Here it
    produces a structured report based on the available clues.
    """

    def __init__(
        self,
        person_id: str,
        person_data: Dict[str, Any],
        name: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(person_id, person_data, name or f"Scout-{person_id}", config)
        self.discoveries: List[Dict[str, Any]] = []

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extend base dispatch with ``run_discovery`` action.
        """
        if input_data.get("action") == "run_discovery":
            return self.run_discovery()
        return super().process(input_data)

    def run_discovery(self) -> Dict[str, Any]:
        """
        Execute the discovery cycle for this lineage.

        Steps:
        1. Collect distilled knowledge from all descendants (already in
           ``self._collected_knowledge`` by the time this is called).
        2. Derive search clues from the accumulated briefing.
        3. Search for new relatives (simulated here; extend for real APIs).
        4. Package findings into a discovery report.
        5. Relay the report back through the descendant chain.

        Returns:
            Discovery report dict.
        """
        clues = self._derive_clues()
        new_relatives = self._search_for_relatives(clues)

        report = {
            "scout_id": self.person_id,
            "scout_name": self.person_data.get("name"),
            "clues_used": clues,
            "new_relatives_found": new_relatives,
            "total_found": len(new_relatives),
            "status": "completed",
        }

        self.discoveries.append(report)
        self.remember({"event": "discovery_run", "findings": len(new_relatives)})

        # Relay report downward through the chain
        for child in self.child_agents:
            child.process({"action": "relay_report", "report": report})

        return report

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def _derive_clues(self) -> List[Dict[str, Any]]:
        """
        Derive actionable search clues from the distilled descendant knowledge.

        Clues include surnames, birth/death locations, date ranges, occupations,
        and any free-text notes that might hint at undiscovered branches.
        """
        clues: List[Dict[str, Any]] = []

        # Own data
        person = self.person_data
        if person.get("birth_place"):
            clues.append({"type": "location", "value": person["birth_place"], "source": self.person_id})
        if person.get("name"):
            surname = self._extract_surname(person["name"])
            if surname:
                clues.append({"type": "surname", "value": surname, "source": self.person_id})
        for note in person.get("notes", []):
            if note:
                clues.append({"type": "note", "value": note, "source": self.person_id})

        # Descendant contributions
        for contribution in self._collected_knowledge:
            if contribution.get("birth_place"):
                clues.append({
                    "type": "location",
                    "value": contribution["birth_place"],
                    "source": contribution.get("person_id"),
                })
            if contribution.get("name"):
                surname = self._extract_surname(contribution["name"])
                if surname:
                    clues.append({
                        "type": "surname",
                        "value": surname,
                        "source": contribution.get("person_id"),
                    })
            for note in contribution.get("notes", []):
                if note:
                    clues.append({
                        "type": "note",
                        "value": note,
                        "source": contribution.get("person_id"),
                    })

        # Deduplicate by (type, value)
        seen = set()
        unique_clues: List[Dict[str, Any]] = []
        for clue in clues:
            key = (clue["type"], clue["value"])
            if key not in seen:
                seen.add(key)
                unique_clues.append(clue)

        return unique_clues

    def _search_for_relatives(
        self, clues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Search for new relatives based on derived clues.

        This base implementation returns a structured placeholder describing
        what *would* be searched.  Override or extend this method to plug in
        real Oracle / archive queries.

        Args:
            clues: List of clue dicts from ``_derive_clues``.

        Returns:
            List of candidate relative dicts.
        """
        candidates: List[Dict[str, Any]] = []

        surnames = [c["value"] for c in clues if c["type"] == "surname"]
        locations = [c["value"] for c in clues if c["type"] == "location"]
        notes = [c["value"] for c in clues if c["type"] == "note"]

        if surnames or locations:
            candidates.append({
                "type": "search_target",
                "description": (
                    f"Archive/DNA search for surname(s) {surnames} "
                    f"in location(s) {locations}"
                ),
                "surnames": surnames,
                "locations": locations,
                "confidence": "pending",
                "notes_hints": notes,
            })

        return candidates

    @staticmethod
    def _extract_surname(full_name: Optional[str]) -> Optional[str]:
        """Return the last word of a full name as a rough surname heuristic."""
        if not full_name:
            return None
        parts = full_name.strip().split()
        return parts[-1] if parts else None


# ---------------------------------------------------------------------------
# FamilyTreeManager
# ---------------------------------------------------------------------------


class FamilyTreeManager(BaseAgent):
    """
    Root orchestrator for the entire family tree agent hierarchy.

    Responsibilities:
    - Import tree data from the normalised format produced by importers.
    - Construct the network of FamilyNodeAgent / LineageScoutAgent instances.
    - Trigger the discovery cycle: propagate knowledge downward → scouts →
      relay reports upward.
    - Collect and return the final distilled intelligence from all scouts.

    The manager itself represents the "tree creator" generation and acts as
    the ultimate recipient of all distilled knowledge and discovery reports.
    """

    def __init__(
        self,
        name: str = "FamilyTreeManager",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name, config)
        # person_id → FamilyNodeAgent (or LineageScoutAgent)
        self._nodes: Dict[str, FamilyNodeAgent] = {}
        self._root_nodes: List[FamilyNodeAgent] = []  # no parents
        self._leaf_nodes: List[FamilyNodeAgent] = []  # no children (scouts)
        self._discovery_reports: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch high-level actions.

        Supported actions:
        - ``load`` — load a normalised tree dict.
        - ``run_discovery`` — execute a full discovery cycle.
        - ``status`` — return manager status.
        - ``get_node`` — get status for a specific node.
        """
        action = input_data.get("action", "status")

        if action == "load":
            return self.load_tree(input_data.get("data", {}))
        if action == "run_discovery":
            return self.run_discovery_cycle()
        if action == "get_node":
            return self._get_node_status(input_data.get("person_id", ""))
        return self.get_status()

    # ------------------------------------------------------------------
    # Tree loading
    # ------------------------------------------------------------------

    def load_tree(self, tree_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the agent hierarchy from a normalised tree dict.

        Args:
            tree_data: Dict produced by GEDCOMImporter, JSONImporter, or
                       Archivist.  Must contain ``individuals`` and
                       ``relationships`` lists.

        Returns:
            Summary of the loaded tree.
        """
        self._nodes = {}
        self._root_nodes = []
        self._leaf_nodes = []

        individuals = tree_data.get("individuals", [])
        relationships = tree_data.get("relationships", [])

        # Create a node agent for every individual
        for person in individuals:
            pid = str(person.get("id", ""))
            if not pid:
                continue
            node = FamilyNodeAgent(
                person_id=pid,
                person_data=person,
                name=f"Node-{person.get('name', pid)}",
            )
            self._nodes[pid] = node

        # Wire parent–child relationships
        for rel in relationships:
            if rel.get("type") != "parent":
                continue
            parent_id = str(rel.get("parent", ""))
            child_id = str(rel.get("child", ""))
            role = rel.get("parent_role", "")

            parent_node = self._nodes.get(parent_id)
            child_node = self._nodes.get(child_id)

            if not parent_node or not child_node:
                continue

            if role == "mother":
                child_node.set_mother(parent_node)
            elif role == "father":
                child_node.set_father(parent_node)
            else:
                # Generic parent — attach as father if father slot is free,
                # otherwise as mother.
                if child_node.father_agent is None:
                    child_node.set_father(parent_node)
                else:
                    child_node.set_mother(parent_node)

        # Identify root nodes (oldest generation — no parents → scouts)
        # and leaf nodes (youngest — no children → starting generation)
        for node in self._nodes.values():
            has_parents = node.mother_agent is not None or node.father_agent is not None
            has_children = bool(node.child_agents)

            if not has_parents:
                # Promote to LineageScoutAgent
                scout = LineageScoutAgent(
                    person_id=node.person_id,
                    person_data=node.person_data,
                    name=f"Scout-{node.person_data.get('name', node.person_id)}",
                    config=node.config,
                )
                scout.child_agents = node.child_agents
                scout._collected_knowledge = node._collected_knowledge
                scout.memory = node.memory
                # Re-wire children to point to the scout
                for child in scout.child_agents:
                    if child.mother_agent and child.mother_agent.person_id == scout.person_id:
                        child.mother_agent = scout
                    if child.father_agent and child.father_agent.person_id == scout.person_id:
                        child.father_agent = scout
                self._nodes[node.person_id] = scout
                self._root_nodes.append(scout)

            if not has_children:
                self._leaf_nodes.append(self._nodes[node.person_id])

        summary = {
            "status": "loaded",
            "source": tree_data.get("source", "unknown"),
            "total_nodes": len(self._nodes),
            "scout_nodes": len(self._root_nodes),
            "youngest_nodes": len(self._leaf_nodes),
        }

        self.remember({"event": "tree_loaded", **summary})
        return summary

    # ------------------------------------------------------------------
    # Discovery cycle
    # ------------------------------------------------------------------

    def run_discovery_cycle(self) -> Dict[str, Any]:
        """
        Execute a full discovery cycle across the entire tree.

        Steps:
        1. **Knowledge propagation** — starting from the youngest generation,
           each node distils its knowledge and contributes it to its parents.
           This continues generation by generation until the scouts at the top
           of each lineage receive the fully-accumulated briefing.
        2. **Scout discovery** — each LineageScoutAgent runs its discovery
           search using the accumulated clues.
        3. **Report relay** — scouts relay their findings back through the
           chain.  The manager collects all reports.

        Returns:
            Aggregated discovery results.
        """
        if not self._nodes:
            return {"error": "No tree loaded. Call load_tree() first."}

        # Step 1: propagate knowledge from youngest → oldest
        self._propagate_knowledge()

        # Step 2 & 3: run discovery on each scout and collect reports
        scout_reports = []
        for node in self._root_nodes:
            if isinstance(node, LineageScoutAgent):
                report = node.run_discovery()
                scout_reports.append(report)
                self._discovery_reports.append(report)

        total_found = sum(r.get("total_found", 0) for r in scout_reports)

        result = {
            "status": "completed",
            "scouts_activated": len(scout_reports),
            "total_discoveries": total_found,
            "scout_reports": scout_reports,
        }

        self.remember({"event": "discovery_cycle", **result})
        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_node(self, person_id: str) -> Optional[FamilyNodeAgent]:
        """Return the agent for a specific person ID, or None."""
        return self._nodes.get(person_id)

    def get_all_nodes(self) -> Dict[str, FamilyNodeAgent]:
        """Return all person-id → agent mappings."""
        return dict(self._nodes)

    def get_scouts(self) -> List[LineageScoutAgent]:
        """Return all LineageScoutAgent instances."""
        return [n for n in self._root_nodes if isinstance(n, LineageScoutAgent)]

    def get_status(self) -> Dict[str, Any]:
        base = super().get_status()
        base.update({
            "total_nodes": len(self._nodes),
            "scout_nodes": len(self._root_nodes),
            "youngest_nodes": len(self._leaf_nodes),
            "discovery_cycles_run": len(self._discovery_reports),
        })
        return base

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _propagate_knowledge(self) -> None:
        """
        Propagate knowledge from the youngest generation upward to the scouts.

        Uses a topological sort so that each node contributes to its parents
        only after all of its own children have contributed to it.
        """
        # Build a directed graph: edge child → parent (knowledge flows up)
        g: nx.DiGraph = nx.DiGraph()
        for pid, node in self._nodes.items():
            g.add_node(pid)
            if node.mother_agent:
                g.add_edge(pid, node.mother_agent.person_id)
            if node.father_agent:
                g.add_edge(pid, node.father_agent.person_id)

        # Process in topological order (leaves first, roots last)
        try:
            order = list(nx.topological_sort(g))
        except nx.NetworkXUnfeasible:
            # Cycle in the data — process in insertion order as fallback
            order = list(self._nodes.keys())

        for pid in order:
            node = self._nodes.get(pid)
            if node:
                node.contribute_knowledge_to_parents()

    def _get_node_status(self, person_id: str) -> Dict[str, Any]:
        node = self._nodes.get(person_id)
        if node is None:
            return {"error": f"Person '{person_id}' not found"}
        return node.get_status()
