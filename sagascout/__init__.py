"""
SagaScout: Autonomous Lineage Intelligence for DNA, Genealogy, and Global Discovery

A comprehensive ecosystem of specialized agents for genealogical research:
- Scouts: DNA match analysis and clustering
- Archivists: Family tree parsing, merging, and relationship inference
- Oracles: Multilingual web research across countries and archives
- Diplomats: Initial outreach and communication with DNA matches
- FamilyTreeManager: Hierarchical family-tree agent system with lineage scouts
"""

__version__ = "0.1.0"

from sagascout.agents.scout import Scout
from sagascout.agents.archivist import Archivist
from sagascout.agents.oracle import Oracle
from sagascout.agents.diplomat import Diplomat
from sagascout.agents.family_tree import (
    FamilyTreeManager,
    FamilyNodeAgent,
    LineageScoutAgent,
)

__all__ = [
    "Scout",
    "Archivist",
    "Oracle",
    "Diplomat",
    "FamilyTreeManager",
    "FamilyNodeAgent",
    "LineageScoutAgent",
]