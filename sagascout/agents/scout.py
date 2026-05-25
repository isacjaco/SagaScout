"""Scout agent for DNA match analysis and clustering."""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sagascout.core.base_agent import BaseAgent
from sagascout.utils.dna_analysis import DNAAnalyzer


class Scout(BaseAgent):
    """
    Scout agent specializes in DNA match analysis and clustering.
    
    Capabilities:
    - Analyze DNA match data
    - Cluster matches by genetic similarity
    - Identify relationship patterns
    - Calculate shared centiMorgans (cM)
    """

    def __init__(self, name: str = "Scout", config: Dict[str, Any] = None):
        """
        Initialize Scout agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary
        """
        super().__init__(name, config)
        self.matches = []
        self.clusters = {}

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process DNA match data.

        Args:
            input_data: Dictionary containing DNA match information
                - matches: List of DNA match records
                - threshold_cm: Minimum cM threshold for clustering

        Returns:
            Dictionary with analysis results
        """
        matches = input_data.get("matches", [])
        threshold_cm = input_data.get("threshold_cm", 20)

        self.matches = matches
        self.clusters = self.cluster_matches(matches, threshold_cm)

        result = {
            "total_matches": len(matches),
            "clusters": self.clusters,
            "cluster_count": len(self.clusters),
            "summary": self._generate_summary(),
        }

        # Remember this analysis
        self.remember({
            "event": "dna_analysis",
            "timestamp": input_data.get("timestamp", "unknown"),
            "match_count": len(matches),
            "cluster_count": len(self.clusters),
        })

        return result

    def cluster_matches(
        self, matches: List[Dict[str, Any]], threshold_cm: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cluster DNA matches based on shared centiMorgans.

        Args:
            matches: List of DNA match records
            threshold_cm: Minimum cM threshold for clustering

        Returns:
            Dictionary of clusters
        """
        clusters = {}

        for match in matches:
            shared_cm = match.get("shared_cm", 0)
            
            # Determine cluster based on cM range
            if shared_cm >= 3500:
                cluster_key = "immediate_family"
            elif shared_cm >= 2000:
                cluster_key = "close_family"
            elif shared_cm >= 500:
                cluster_key = "1st_2nd_cousins"
            elif shared_cm >= 200:
                cluster_key = "2nd_3rd_cousins"
            elif shared_cm >= threshold_cm:
                cluster_key = "distant_cousins"
            else:
                continue

            if cluster_key not in clusters:
                clusters[cluster_key] = []
            
            clusters[cluster_key].append(match)

        return clusters

    def analyze_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single DNA match.

        Args:
            match: DNA match record

        Returns:
            Analysis results for the match
        """
        shared_cm = match.get("shared_cm", 0)
        segments = match.get("segments", 0)

        # Estimate relationship
        relationship = self._estimate_relationship(shared_cm)
        
        # Calculate confidence
        confidence = self._calculate_confidence(shared_cm, segments)

        return {
            "match_id": match.get("id"),
            "name": match.get("name"),
            "shared_cm": shared_cm,
            "segments": segments,
            "estimated_relationship": relationship,
            "confidence": confidence,
        }

    def _estimate_relationship(self, shared_cm: float) -> str:
        """Estimate relationship based on shared centiMorgans."""
        return DNAAnalyzer.estimate_relationship(shared_cm)

    def _calculate_confidence(self, shared_cm: float, segments: int) -> float:
        """Calculate confidence score for relationship estimate."""
        # Higher cM and more segments = higher confidence
        cm_factor = min(shared_cm / 3500, 1.0)
        segment_factor = min(segments / 20, 1.0) if segments > 0 else 0.5
        
        return (cm_factor * 0.7 + segment_factor * 0.3) * 100

    def _generate_summary(self) -> str:
        """Generate a summary of the analysis."""
        summary_parts = [
            f"Analyzed {len(self.matches)} DNA matches",
            f"Identified {len(self.clusters)} distinct clusters",
        ]
        
        for cluster_name, cluster_matches in self.clusters.items():
            summary_parts.append(
                f"  - {cluster_name}: {len(cluster_matches)} matches"
            )
        
        return " | ".join(summary_parts)

    def get_cluster(self, cluster_key: str) -> List[Dict[str, Any]]:
        """
        Get matches in a specific cluster.

        Args:
            cluster_key: Cluster identifier

        Returns:
            List of matches in the cluster
        """
        return self.clusters.get(cluster_key, [])

    def find_shared_matches(
        self, match_id1: str, match_id2: str
    ) -> List[Dict[str, Any]]:
        """
        Find shared matches between two DNA matches.

        Args:
            match_id1: First match ID
            match_id2: Second match ID

        Returns:
            List of shared matches
        """
        # Placeholder for shared match logic
        # In a real implementation, this would query DNA database
        return []

    def find_shared_matches_from_data(
        self,
        match_id1: str,
        match_id2: str,
        shared_matches_map: Dict[str, List[str]],
    ) -> List[Dict[str, Any]]:
        """
        Find shared matches between two DNA matches using a provided mapping.

        Args:
            match_id1: First match ID
            match_id2: Second match ID
            shared_matches_map: Dictionary mapping match ID -> list of match IDs
                that share DNA with the key match (same format used by
                :meth:`~sagascout.utils.dna_analysis.GeneticClustering.identify_triangulation_groups`)

        Returns:
            List of match dictionaries from ``self.matches`` that are shared
            between *match_id1* and *match_id2*
        """
        matches_of_1 = set(shared_matches_map.get(match_id1, []))
        matches_of_2 = set(shared_matches_map.get(match_id2, []))
        shared_ids = matches_of_1 & matches_of_2

        # Build a quick lookup from id -> full match record
        match_lookup = {m.get("id"): m for m in self.matches}
        return [match_lookup[mid] for mid in shared_ids if mid in match_lookup]

    # ------------------------------------------------------------------ #
    # CSV import                                                           #
    # ------------------------------------------------------------------ #

    def import_ancestry_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Import DNA matches from an AncestryDNA match CSV export.

        Expected columns (case-insensitive):
        ``Match Name``, ``Shared DNA``, ``Shared Segments``,
        ``Last Name``, ``First Name`` (alternative to Match Name).

        Args:
            filepath: Path to the CSV file

        Returns:
            Dictionary with import results
        """
        path = Path(filepath)
        if not path.is_file():
            return {"error": f"File not found: {filepath}"}

        imported = []
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            # Normalise header names to lowercase
            for row in reader:
                row_lower = {k.lower().strip(): v for k, v in row.items()}
                name = (
                    row_lower.get("match name")
                    or f"{row_lower.get('first name', '')} {row_lower.get('last name', '')}".strip()
                    or "Unknown"
                )
                # Shared DNA may look like "850 cM", "850 CM", or just "850"
                raw_cm = row_lower.get("shared dna", "0").upper().replace("CM", "").replace(",", "").strip()
                try:
                    shared_cm = float(raw_cm)
                except ValueError:
                    shared_cm = 0.0
                raw_segs = row_lower.get("shared segments", "0").strip()
                try:
                    segments = int(raw_segs)
                except ValueError:
                    segments = 0
                match = {
                    "id": f"anc_{len(self.matches) + len(imported)}",
                    "name": name,
                    "shared_cm": shared_cm,
                    "segments": segments,
                    "source": "ancestry",
                }
                imported.append(match)

        self.matches.extend(imported)
        return {
            "status": "success",
            "imported": len(imported),
            "total_matches": len(self.matches),
        }

    def import_23andme_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Import DNA matches from a 23andMe match CSV export.

        Expected columns (case-insensitive):
        ``Name``, ``DNA Shared``, ``Segments``.

        Args:
            filepath: Path to the CSV file

        Returns:
            Dictionary with import results
        """
        path = Path(filepath)
        if not path.is_file():
            return {"error": f"File not found: {filepath}"}

        imported = []
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row_lower = {k.lower().strip(): v for k, v in row.items()}
                name = row_lower.get("name", "Unknown")
                raw_cm = row_lower.get("dna shared", "0").replace("%", "").strip()
                try:
                    shared_cm = float(raw_cm)
                except ValueError:
                    shared_cm = 0.0
                raw_segs = row_lower.get("segments", "0").strip()
                try:
                    segments = int(raw_segs)
                except ValueError:
                    segments = 0
                match = {
                    "id": f"23me_{len(self.matches) + len(imported)}",
                    "name": name,
                    "shared_cm": shared_cm,
                    "segments": segments,
                    "source": "23andme",
                }
                imported.append(match)

        self.matches.extend(imported)
        return {
            "status": "success",
            "imported": len(imported),
            "total_matches": len(self.matches),
        }

    # ------------------------------------------------------------------ #
    # JSON serialization                                                   #
    # ------------------------------------------------------------------ #

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the current match state to a JSON-compatible dictionary.

        Returns:
            Dictionary containing matches and clusters
        """
        return {
            "matches": self.matches,
            "clusters": self.clusters,
        }

    def save_to_file(self, filepath: str) -> None:
        """
        Save match state to a JSON file.

        Args:
            filepath: Destination file path
        """
        Path(filepath).write_text(
            json.dumps(self.to_json(), indent=2), encoding="utf-8"
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any], name: str = "Scout",
                  config: Dict[str, Any] = None) -> "Scout":
        """
        Restore a Scout from a previously serialized dictionary.

        Args:
            data: Dictionary as returned by :meth:`to_json`
            name: Agent name
            config: Optional configuration

        Returns:
            Scout instance populated with the saved state
        """
        scout = cls(name=name, config=config)
        scout.matches = data.get("matches", [])
        scout.clusters = data.get("clusters", {})
        return scout

    @classmethod
    def load_from_file(cls, filepath: str, name: str = "Scout",
                       config: Dict[str, Any] = None) -> "Scout":
        """
        Load a Scout from a JSON file saved by :meth:`save_to_file`.

        Args:
            filepath: Source file path
            name: Agent name
            config: Optional configuration

        Returns:
            Scout instance populated with the saved state
        """
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        return cls.from_json(data, name=name, config=config)
