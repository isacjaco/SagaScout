"""DNA analysis utilities for SagaScout."""

from typing import List, Dict, Any, Tuple
import numpy as np


class DNAAnalyzer:
    """Utilities for DNA match analysis and calculations."""

    @staticmethod
    def calculate_relationship_probability(
        shared_cm: float, segments: int
    ) -> Dict[str, float]:
        """
        Calculate probability of various relationships based on shared DNA.

        Args:
            shared_cm: Shared centiMorgans
            segments: Number of DNA segments

        Returns:
            Dictionary of relationship probabilities
        """
        probabilities = {}

        # Define relationship ranges and their probabilities
        relationships = [
            ("Parent/Child", 3400, 3700, 1.0),
            ("Sibling", 2300, 2900, 0.95),
            ("Grandparent/Grandchild", 1700, 2200, 0.9),
            ("Uncle/Aunt", 1300, 2300, 0.85),
            ("Half Sibling", 1300, 2200, 0.8),
            ("1st Cousin", 500, 1300, 0.75),
            ("1st Cousin Once Removed", 220, 700, 0.7),
            ("2nd Cousin", 90, 360, 0.65),
            ("2nd Cousin Once Removed", 45, 200, 0.6),
            ("3rd Cousin", 20, 140, 0.5),
        ]

        for rel_name, min_cm, max_cm, base_prob in relationships:
            if min_cm <= shared_cm <= max_cm:
                # Calculate probability based on how close to center of range
                center = (min_cm + max_cm) / 2
                distance = abs(shared_cm - center)
                range_size = max_cm - min_cm
                position_factor = 1 - (distance / (range_size / 2)) * 0.3
                
                probabilities[rel_name] = base_prob * position_factor

        return probabilities

    @staticmethod
    def estimate_generations(shared_cm: float) -> Tuple[int, int]:
        """
        Estimate number of generations between two individuals.

        Args:
            shared_cm: Shared centiMorgans

        Returns:
            Tuple of (min_generations, max_generations)
        """
        if shared_cm >= 3400:
            return (1, 1)  # Parent/Child
        elif shared_cm >= 2300:
            return (2, 2)  # Sibling or Grandparent
        elif shared_cm >= 1300:
            return (2, 3)  # Uncle/Aunt or Half Sibling
        elif shared_cm >= 500:
            return (3, 4)  # 1st Cousin range
        elif shared_cm >= 200:
            return (4, 5)  # 2nd Cousin range
        elif shared_cm >= 90:
            return (5, 6)  # 3rd Cousin range
        elif shared_cm >= 20:
            return (6, 8)  # 4th-5th Cousin range
        else:
            return (7, 10)  # Distant cousins

    @staticmethod
    def cluster_by_similarity(
        matches: List[Dict[str, Any]], threshold: float = 0.8
    ) -> List[List[Dict[str, Any]]]:
        """
        Cluster DNA matches by similarity.

        Args:
            matches: List of DNA match records
            threshold: Similarity threshold for clustering

        Returns:
            List of match clusters
        """
        if not matches:
            return []

        # Simple clustering based on shared cM ranges
        clusters = []
        sorted_matches = sorted(
            matches, key=lambda x: x.get("shared_cm", 0), reverse=True
        )

        current_cluster = [sorted_matches[0]]
        current_cm = sorted_matches[0].get("shared_cm", 0)

        for match in sorted_matches[1:]:
            match_cm = match.get("shared_cm", 0)
            
            # If within 20% of current cluster average, add to cluster
            if abs(match_cm - current_cm) / max(current_cm, 1) < 0.2:
                current_cluster.append(match)
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = [match]
                current_cm = match_cm

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    @staticmethod
    def calculate_shared_ancestor_distance(
        cm1: float, cm2: float
    ) -> Dict[str, Any]:
        """
        Calculate distance to shared ancestor for two matches.

        Args:
            cm1: Shared cM with first match
            cm2: Shared cM with second match

        Returns:
            Dictionary with distance information
        """
        gen1 = DNAAnalyzer.estimate_generations(cm1)
        gen2 = DNAAnalyzer.estimate_generations(cm2)

        return {
            "match1_generations": gen1,
            "match2_generations": gen2,
            "estimated_ancestor_generation": max(gen1[0], gen2[0]),
            "confidence": "medium" if gen1[1] - gen1[0] <= 2 else "low",
        }


class GeneticClustering:
    """Advanced clustering algorithms for DNA matches."""

    @staticmethod
    def hierarchical_cluster(
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform hierarchical clustering on DNA matches.

        Args:
            matches: List of DNA match records

        Returns:
            Hierarchical cluster structure
        """
        if len(matches) < 2:
            return {"clusters": [matches], "hierarchy": {}}

        # Sort by shared cM
        sorted_matches = sorted(
            matches, key=lambda x: x.get("shared_cm", 0), reverse=True
        )

        # Build simple hierarchy
        hierarchy = {
            "root": {
                "immediate_family": [],
                "close_family": [],
                "extended_family": [],
                "distant_relatives": [],
            }
        }

        for match in sorted_matches:
            cm = match.get("shared_cm", 0)
            if cm >= 2000:
                hierarchy["root"]["immediate_family"].append(match)
            elif cm >= 500:
                hierarchy["root"]["close_family"].append(match)
            elif cm >= 90:
                hierarchy["root"]["extended_family"].append(match)
            else:
                hierarchy["root"]["distant_relatives"].append(match)

        return {
            "clusters": [
                hierarchy["root"]["immediate_family"],
                hierarchy["root"]["close_family"],
                hierarchy["root"]["extended_family"],
                hierarchy["root"]["distant_relatives"],
            ],
            "hierarchy": hierarchy,
        }

    @staticmethod
    def identify_triangulation_groups(
        matches: List[Dict[str, Any]], shared_matches: Dict[str, List[str]]
    ) -> List[List[str]]:
        """
        Identify triangulation groups (matches who all match each other).

        Args:
            matches: List of DNA match records
            shared_matches: Dictionary mapping match IDs to their shared matches

        Returns:
            List of triangulation groups (match ID lists)
        """
        groups = []
        processed = set()

        for match in matches:
            match_id = match.get("id")
            if match_id in processed:
                continue

            # Find matches who share with this match
            shared = shared_matches.get(match_id, [])
            
            # Check if they all share with each other (triangulation)
            group = [match_id]
            for shared_id in shared:
                if shared_id not in processed:
                    # Verify triangulation
                    their_shared = shared_matches.get(shared_id, [])
                    if all(m in their_shared for m in group):
                        group.append(shared_id)

            if len(group) > 1:
                groups.append(group)
                processed.update(group)

        return groups
