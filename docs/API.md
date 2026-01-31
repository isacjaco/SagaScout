# SagaScout API Reference

## Table of Contents
- [Agents](#agents)
  - [Scout](#scout-agent)
  - [Archivist](#archivist-agent)
  - [Oracle](#oracle-agent)
  - [Diplomat](#diplomat-agent)
- [Utilities](#utilities)
  - [DNA Analysis](#dna-analysis)
  - [Narrative Memory](#narrative-memory)
  - [Governance Rituals](#governance-rituals)

---

## Agents

### Scout Agent

DNA match analysis and clustering specialist.

#### Constructor

```python
Scout(name: str = "Scout", config: Dict[str, Any] = None)
```

**Parameters:**
- `name` (str): Agent name
- `config` (dict): Optional configuration

#### Methods

##### `process(input_data: Dict[str, Any]) -> Dict[str, Any]`

Process DNA match data and perform clustering.

**Input:**
```python
{
    "matches": [
        {
            "id": str,           # Unique match identifier
            "name": str,         # Match name
            "shared_cm": float,  # Shared centiMorgans
            "segments": int      # Number of DNA segments
        }
    ],
    "threshold_cm": float,       # Minimum cM for clustering (default: 20)
    "timestamp": str             # Optional timestamp
}
```

**Output:**
```python
{
    "total_matches": int,
    "clusters": {
        "immediate_family": [...],
        "close_family": [...],
        "1st_2nd_cousins": [...],
        "2nd_3rd_cousins": [...],
        "distant_cousins": [...]
    },
    "cluster_count": int,
    "summary": str
}
```

##### `analyze_match(match: Dict[str, Any]) -> Dict[str, Any]`

Analyze a single DNA match in detail.

**Returns:**
```python
{
    "match_id": str,
    "name": str,
    "shared_cm": float,
    "segments": int,
    "estimated_relationship": str,
    "confidence": float  # 0-100
}
```

##### `get_cluster(cluster_key: str) -> List[Dict[str, Any]]`

Get all matches in a specific cluster.

**Parameters:**
- `cluster_key` (str): One of "immediate_family", "close_family", "1st_2nd_cousins", "2nd_3rd_cousins", "distant_cousins"

---

### Archivist Agent

Family tree parsing, merging, and relationship inference specialist.

#### Constructor

```python
Archivist(name: str = "Archivist", config: Dict[str, Any] = None)
```

#### Methods

##### `process(input_data: Dict[str, Any]) -> Dict[str, Any]`

Process family tree operations.

**Input for "parse" action:**
```python
{
    "action": "parse",
    "data": {
        "individuals": [
            {
                "id": str,
                "name": str,
                "birth_year": int,
                "birth_date": str,
                "death_date": str,
                # ... other attributes
            }
        ],
        "relationships": [
            {
                "parent": str,  # Parent ID
                "child": str,   # Child ID
                "type": str     # Relationship type
            }
        ]
    }
}
```

**Output:**
```python
{
    "status": "success",
    "individuals_added": int,
    "relationships_added": int,
    "total_nodes": int,
    "total_edges": int
}
```

**Input for "merge" action:**
```python
{
    "action": "merge",
    "data": {
        "individuals": [...],  # Same format as parse
        "relationships": [...]
    }
}
```

**Output:**
```python
{
    "status": "success",
    "merged_individuals": int,
    "new_individuals": int,
    "conflicts": [
        {
            "person_id": str,
            "conflicts": {
                "field_name": {
                    "existing": Any,
                    "new": Any
                }
            }
        }
    ],
    "total_nodes": int,
    "total_edges": int
}
```

**Input for "infer" action:**
```python
{
    "action": "infer",
    "data": {
        "person1": str,  # First person ID
        "person2": str   # Second person ID
    }
}
```

**Output:**
```python
{
    "person1": str,
    "person2": str,
    "relationship": str,
    "path": [str],      # Path of person IDs
    "path_length": int
}
```

**Input for "query" action:**
```python
{
    "action": "query",
    "data": {
        "type": str,      # "ancestors", "descendants", "siblings", "statistics"
        "person_id": str  # Required for all except "statistics"
    }
}
```

---

### Oracle Agent

Multilingual research and document extraction specialist.

#### Constructor

```python
Oracle(name: str = "Oracle", config: Dict[str, Any] = None)
```

#### Methods

##### `process(input_data: Dict[str, Any]) -> Dict[str, Any]`

Process research or extraction requests.

**Input for "research" action:**
```python
{
    "action": "research",
    "query": str,
    "languages": [str],  # Language codes (e.g., ["en", "es", "fr"])
    "countries": [str]   # Country codes (e.g., ["US", "MX"])
}
```

**Output:**
```python
{
    "status": "success" | "cached",
    "query": str,
    "languages": [str],
    "results": [
        {
            "language": str,
            "query": str,
            "sources": [
                {
                    "id": str,
                    "language": str,
                    "type": str,
                    "reliability": float,
                    "url": str
                }
            ],
            "summary": str
        }
    ],
    "total_sources": int
}
```

**Input for "extract" action:**
```python
{
    "action": "extract",
    "document": {
        "id": str,
        "name": str,
        "date": str,
        "place": str,
        # ... document fields
    },
    "type": str  # "birth_record", "death_record", "marriage_record", "census", "general"
}
```

**Input for "search_archives" action:**
```python
{
    "action": "search_archives",
    "query": str,
    "archives": [str],  # Optional: specific archives
    "countries": [str]  # Required: country codes
}
```

**Input for "translate" action:**
```python
{
    "action": "translate",
    "query": str,
    "languages": [str]  # Target languages
}
```

##### `get_supported_languages() -> List[str]`

Get list of supported language codes.

##### `get_documents() -> List[Dict[str, Any]]`

Get all extracted documents.

---

### Diplomat Agent

Cross-cultural communication and outreach specialist.

#### Constructor

```python
Diplomat(name: str = "Diplomat", config: Dict[str, Any] = None)
```

#### Methods

##### `process(input_data: Dict[str, Any]) -> Dict[str, Any]`

Process communication requests.

**Input for "draft" action:**
```python
{
    "action": "draft",
    "recipient": {
        "id": str,
        "name": str,
        "country": str  # Country code
    },
    "purpose": str,  # "initial_contact", "share_research", "request_information"
    "language": str,
    "context": dict  # Optional context (e.g., {"shared_ancestor": "..."})
}
```

**Output:**
```python
{
    "status": "success",
    "draft": {
        "recipient": dict,
        "language": str,
        "purpose": str,
        "subject": str,
        "body": str,
        "cultural_notes": dict,
        "tone": str
    },
    "recommendations": [str]
}
```

**Input for "send" action:**
```python
{
    "action": "send",
    "message": dict,  # Message from draft
    "timestamp": str
}
```

**Input for "respond" action:**
```python
{
    "action": "respond",
    "original_message": dict,
    "sender": dict,
    "tone": str  # Optional: "friendly", "formal", etc.
}
```

**Input for "analyze_culture" action:**
```python
{
    "action": "analyze_culture",
    "country": str,
    "situation": str  # Optional: context for analysis
}
```

**Output:**
```python
{
    "status": "success",
    "analysis": {
        "country": str,
        "communication_style": str,  # "direct" or "indirect"
        "formality_level": str,      # "low", "medium", "high"
        "greeting_customs": str,
        "taboo_topics": [str],
        "best_practices": [str]
    },
    "recommendations": [str]
}
```

##### `get_communication_history(contact_id: str = None) -> List[Dict[str, Any]]`

Get communication history, optionally filtered by contact.

##### `get_contact_info(contact_id: str) -> Optional[Dict[str, Any]]`

Get information about a specific contact.

---

## Utilities

### DNA Analysis

#### DNAAnalyzer

##### `calculate_relationship_probability(shared_cm: float, segments: int) -> Dict[str, float]`

Calculate probability of various relationships.

**Returns:** Dictionary mapping relationship names to probabilities (0.0-1.0)

##### `estimate_generations(shared_cm: float) -> Tuple[int, int]`

Estimate number of generations between individuals.

**Returns:** Tuple of (min_generations, max_generations)

##### `cluster_by_similarity(matches: List[Dict], threshold: float = 0.8) -> List[List[Dict]]`

Cluster DNA matches by similarity.

##### `calculate_shared_ancestor_distance(cm1: float, cm2: float) -> Dict[str, Any]`

Calculate distance to shared ancestor for two matches.

#### GeneticClustering

##### `hierarchical_cluster(matches: List[Dict]) -> Dict[str, Any]`

Perform hierarchical clustering on DNA matches.

##### `identify_triangulation_groups(matches: List[Dict], shared_matches: Dict[str, List[str]]) -> List[List[str]]`

Identify triangulation groups.

---

### Narrative Memory

#### NarrativeMemory

##### Constructor

```python
NarrativeMemory()
```

##### `store_memory(event_type: str, content: Dict, significance: float = 0.5, tags: List[str] = None) -> str`

Store a narrative memory.

**Parameters:**
- `event_type` (str): Type of event (e.g., "discovery", "connection")
- `content` (dict): Event content
- `significance` (float): Importance score (0.0-1.0)
- `tags` (list): Optional tags

**Returns:** Memory ID

##### `recall_memories(query: str = None, event_type: str = None, tags: List[str] = None, min_significance: float = 0.0) -> List[Dict]`

Recall memories based on criteria.

##### `connect_memories(memory_id1: str, memory_id2: str, connection_type: str = "related") -> None`

Create a connection between two memories.

##### `get_memory_narrative(memory_id: str) -> Dict[str, Any]`

Get a memory with its narrative context.

---

### Governance Rituals

#### GovernanceRitual

##### Constructor

```python
GovernanceRitual()
```

##### `create_ritual(name: str, ritual_type: str, participants: List[str], rules: Dict) -> str`

Create a governance ritual.

**Parameters:**
- `name` (str): Ritual name
- `ritual_type` (str): "decision", "coordination", or "review"
- `participants` (list): Agent names
- `rules` (dict): Ritual rules (e.g., {"threshold": 0.66})

**Returns:** Ritual ID

##### `execute_ritual(ritual_id: str, context: Dict) -> Dict[str, Any]`

Execute a governance ritual.

##### `council_decision(topic: str, agents: List[str], votes: Dict[str, str]) -> Dict[str, Any]`

Make a council decision with agent votes.

**Parameters:**
- `topic` (str): Decision topic
- `agents` (list): Participating agents
- `votes` (dict): Agent votes (e.g., {"Agent1": "approve", "Agent2": "reject"})

---

## Error Handling

All methods may raise standard Python exceptions:
- `ValueError`: Invalid input parameters
- `KeyError`: Missing required fields
- `TypeError`: Wrong data types

Agents return error dictionaries when operations fail:
```python
{"error": "Error message"}
```

---

## Example Workflows

### Complete Research Workflow

```python
from sagascout import Scout, Archivist, Oracle, Diplomat

# 1. Analyze DNA
scout = Scout()
dna_results = scout.process({
    "matches": [...],
    "threshold_cm": 20
})

# 2. Build tree
archivist = Archivist()
archivist.process({
    "action": "parse",
    "data": {"individuals": [...], "relationships": [...]}
})

# 3. Research
oracle = Oracle()
research = oracle.process({
    "action": "research",
    "query": "family name",
    "languages": ["en"],
    "countries": ["US"]
})

# 4. Communicate
diplomat = Diplomat()
message = diplomat.process({
    "action": "draft",
    "recipient": {...},
    "purpose": "initial_contact",
    "language": "en"
})
```

---

For more examples, see the `examples/` directory.
