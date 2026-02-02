"""Scout agent for DNA match analysis and clustering."""

from typing import List, Dict, Any, Tuple
import numpy as np
from sagascout.core.base_agent import BaseAgent


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
        cluster_id = 0

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
        if shared_cm >= 3500:
            return "Parent/Child or Identical Twin"
        elif shared_cm >= 2000:
            return "Sibling or Grandparent/Grandchild"
        elif shared_cm >= 1300:
            return "Half Sibling or Uncle/Aunt"
        elif shared_cm >= 500:
            return "1st Cousin or Great-Grandparent"
        elif shared_cm >= 200:
            return "1st-2nd Cousin"
        elif shared_cm >= 90:
            return "2nd-3rd Cousin"
        elif shared_cm >= 20:
            return "3rd-4th Cousin"
        else:
            return "Distant Cousin"

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