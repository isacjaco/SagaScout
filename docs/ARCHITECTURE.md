# SagaScout Architecture

## Overview

SagaScout is a multi-agent system designed for autonomous genealogical research. The architecture follows a modular design with specialized agents that work independently or collaboratively through governance mechanisms.

## System Architecture

```
SagaScout/
├── Core Layer
│   ├── BaseAgent (Abstract base class)
│   └── Agent Memory System
│
├── Agent Layer
│   ├── Scout (DNA Analysis)
│   ├── Archivist (Tree Management)
│   ├── Oracle (Research)
│   └── Diplomat (Communication)
│
├── Utility Layer
│   ├── DNA Analysis Tools
│   ├── Narrative Memory
│   └── Governance Rituals
│
└── Interface Layer
    ├── Python API
    └── Examples

```

## Core Components

### 1. Base Agent (sagascout/core/base_agent.py)

The `BaseAgent` class provides common functionality for all agents:

- **Memory Management**: Store and recall events
- **Status Reporting**: Track agent state
- **Abstract Processing**: Define agent-specific operations

```python
class BaseAgent(ABC):
    def __init__(self, name, config)
    def process(self, input_data) -> Any  # Abstract
    def remember(self, event)
    def recall(self, query=None)
    def get_status()
```

### 2. Agent Layer

#### Scout Agent (sagascout/agents/scout.py)

**Purpose**: DNA match analysis and clustering

**Key Features**:
- Cluster DNA matches by shared centiMorgans (cM)
- Estimate relationships based on genetic data
- Calculate confidence scores
- Identify relationship patterns

**Data Structures**:
```python
{
    "matches": [
        {"id": str, "name": str, "shared_cm": float, "segments": int}
    ],
    "threshold_cm": float
}
```

**Clustering Algorithm**:
- Immediate Family: >= 3500 cM
- Close Family: >= 2000 cM
- 1st-2nd Cousins: >= 500 cM
- 2nd-3rd Cousins: >= 200 cM
- Distant Cousins: >= threshold_cm

#### Archivist Agent (sagascout/agents/archivist.py)

**Purpose**: Family tree parsing, merging, and relationship inference

**Key Features**:
- Parse family tree data from structured formats
- Merge multiple trees with conflict detection
- Infer relationships using graph algorithms (NetworkX)
- Query ancestors, descendants, siblings

**Data Structure**: Directed graph (NetworkX DiGraph)
- Nodes: Individuals with attributes
- Edges: Parent-child relationships

**Operations**:
- `parse`: Add individuals and relationships
- `merge`: Combine trees with conflict detection
- `infer`: Calculate relationship paths
- `query`: Retrieve ancestors, descendants, statistics

#### Oracle Agent (sagascout/agents/oracle.py)

**Purpose**: Multilingual web research and document extraction

**Key Features**:
- Support for 17+ languages
- Archive search across countries
- Document extraction (birth, death, marriage, census)
- Research result caching

**Supported Languages**:
- Western: en, es, fr, de, it, pt, nl, sv, no, da
- Slavic: pl, ru
- Asian: zh, ja, ko
- Middle Eastern: ar, he

**Archive Map**:
- US: Ancestry.com, FamilySearch, MyHeritage
- UK: FindMyPast, TheGenealogist, FreeBMD
- FR: Archives Nationales, Geneanet
- DE: Archion, Ancestry.de
- And more...

#### Diplomat Agent (sagascout/agents/diplomat.py)

**Purpose**: Cross-cultural communication and outreach

**Key Features**:
- Draft culturally-appropriate messages
- Analyze cultural context
- Track communication history
- Provide recommendations

**Cultural Profiles**:
- Communication style (direct/indirect)
- Formality level (low/medium/high)
- Greeting customs
- Taboo topics
- Best practices

**Message Types**:
- initial_contact
- share_research
- request_information

### 3. Utility Layer

#### DNA Analysis (sagascout/utils/dna_analysis.py)

**DNAAnalyzer**:
- `calculate_relationship_probability()`: Statistical analysis
- `estimate_generations()`: Calculate genealogical distance
- `cluster_by_similarity()`: Group similar matches
- `calculate_shared_ancestor_distance()`: Ancestor calculations

**GeneticClustering**:
- `hierarchical_cluster()`: Build cluster hierarchy
- `identify_triangulation_groups()`: Find shared match patterns

#### Narrative Memory (sagascout/utils/narrative_memory.py)

**Purpose**: Store events as narrative memories with context

**Key Features**:
- Store events with emotional significance
- Connect related memories
- Auto-tagging based on content
- Query by type, tags, significance

**Memory Structure**:
```python
{
    "id": str,
    "type": str,
    "content": dict,
    "significance": float (0.0-1.0),
    "tags": [str],
    "timestamp": str,
    "connections": [dict]
}
```

#### Governance Rituals (sagascout/utils/narrative_memory.py)

**Purpose**: Coordinate multi-agent decision-making

**Ritual Types**:
- **decision**: Voting-based decisions with thresholds
- **coordination**: Task assignment and role distribution
- **review**: Peer review and approval processes

**Features**:
- Council-based voting
- Structured decision-making
- Execution history tracking
- Consensus building

## Data Flow

### Typical Research Workflow

1. **DNA Discovery** (Scout)
   ```
   DNA Match Data → Scout.process() → Clustered Matches
   ```

2. **Family Tree Integration** (Archivist)
   ```
   Match Data + Tree Data → Archivist.parse() → Updated Tree
   Tree1 + Tree2 → Archivist.merge() → Merged Tree
   ```

3. **Historical Research** (Oracle)
   ```
   Research Query → Oracle.research() → Sources
   Archive Query → Oracle.search_archives() → Records
   Document → Oracle.extract_document() → Structured Data
   ```

4. **Communication** (Diplomat)
   ```
   Contact Info → Diplomat.draft_message() → Message Draft
   Cultural Context → Diplomat.analyze_culture() → Recommendations
   ```

### Agent Coordination

```
┌──────────┐     ┌─────────────┐     ┌──────────┐
│  Scout   │────▶│ Governance  │◀────│Archivist │
└──────────┘     │   Ritual    │     └──────────┘
     │           └─────────────┘           │
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐     ┌─────────────┐     ┌──────────┐
│  Oracle  │────▶│   Shared    │◀────│ Diplomat │
└──────────┘     │   Memory    │     └──────────┘
                 └─────────────┘
```

## Design Patterns

### 1. Strategy Pattern
Each agent implements the `process()` method differently based on its specialty.

### 2. Template Method Pattern
`BaseAgent` provides the template for agent behavior with customizable processing.

### 3. Observer Pattern
Agents can observe and react to shared memory events.

### 4. Command Pattern
Governance rituals encapsulate actions as commands with execution history.

## Extensibility

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement `process()` method
3. Add agent-specific methods
4. Register in `sagascout/__init__.py`

```python
from sagascout.core.base_agent import BaseAgent

class NewAgent(BaseAgent):
    def process(self, input_data):
        # Custom processing logic
        return result
```

### Adding New Utilities

1. Create module in `sagascout/utils/`
2. Implement standalone functions or classes
3. Export in `sagascout/utils/__init__.py`

### Extending Cultural Profiles

Add new country profiles in `Diplomat._load_cultural_profiles()`:

```python
"COUNTRY_CODE": {
    "communication_style": "direct|indirect",
    "formality_level": "low|medium|high",
    "greeting_customs": "...",
    "taboo_topics": [...],
    "best_practices": [...]
}
```

## Performance Considerations

### Memory Management
- Agents maintain in-memory state
- Use caching for research results (Oracle)
- Narrative memory can grow; implement pruning for production

### Graph Operations
- NetworkX operations are efficient for small-medium trees (<10,000 nodes)
- For larger trees, consider graph database (Neo4j)

### Scalability
- Agents are stateless between `process()` calls
- Can be distributed across processes/machines
- Consider message queues for coordination

## Security Considerations

### Data Privacy
- DNA data is sensitive; implement encryption for storage
- Communication drafts may contain PII
- Implement access controls for tree data

### Input Validation
- Validate all input data structures
- Sanitize user-provided queries
- Prevent injection attacks in document extraction

## Testing Strategy

### Unit Tests
- Test each agent independently
- Test utility functions
- Test memory and governance systems

### Integration Tests
- Test agent coordination
- Test complete workflows
- Test error handling

### Example Tests
See `tests/test_basic.py` for basic functionality tests.

## Future Enhancements

### Planned Features
1. **Database Integration**: Persistent storage for trees and matches
2. **REST API**: Web service interface
3. **Web UI**: Interactive dashboard
4. **Real DNA Integration**: Connect to Ancestry, 23andMe APIs
5. **ML Models**: Improve relationship prediction
6. **Blockchain**: Decentralized tree storage and verification
7. **Mobile App**: iOS/Android clients

### Research Directions
1. Advanced clustering algorithms (DBSCAN, hierarchical)
2. Natural language processing for document extraction
3. Computer vision for document image analysis
4. Graph neural networks for relationship inference
5. Federated learning for privacy-preserving analysis

## References

- **DNA Analysis**: The Shared cM Project (https://thegeneticgenealogist.com)
- **Graph Theory**: NetworkX documentation
- **Genealogy Standards**: GEDCOM format
- **Cultural Communication**: Hofstede's Cultural Dimensions

## Contributing

See the main README.md for contribution guidelines.

## License

MIT License - see LICENSE file.
