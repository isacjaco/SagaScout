# SagaScout
### Autonomous Lineage Intelligence for DNA, Genealogy, and Global Discovery

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

SagaScout is a comprehensive ecosystem of specialized AI agents designed for genealogical research, DNA analysis, and cross-cultural family history discovery. The system combines cutting-edge computational genealogy with narrative-driven memory and governance systems.

## 🌟 Features

### Multi-Agent Ecosystem

SagaScout consists of four specialized agent types, each with unique capabilities:

#### 🔬 **Scout** - DNA Match Analysis
- Analyze DNA match data and calculate relationship probabilities
- Cluster matches by genetic similarity and shared centiMorgans (cM)
- Identify relationship patterns and triangulation groups
- Estimate generations to common ancestors
- Calculate confidence scores for relationship predictions

#### 📚 **Archivist** - Family Tree Management
- Parse family tree data from various formats
- Merge multiple family trees with conflict detection
- Infer relationships between individuals using graph algorithms
- Query ancestors, descendants, and siblings
- Manage complex family structures with NetworkX graphs

#### 🔍 **Oracle** - Multilingual Research
- Conduct web research across 17+ languages
- Search international archives and genealogical databases
- Extract information from birth, death, marriage, and census records
- Navigate cross-border historical records
- Cache research results for efficiency

#### 🤝 **Diplomat** - Cross-Cultural Communication
- Draft culturally-sensitive outreach messages to DNA matches
- Provide communication recommendations based on cultural context
- Analyze message tone and intent
- Support communication in multiple languages
- Maintain contact history and relationship management

### Advanced Utilities

#### DNA Analysis Tools
- **Relationship probability calculator** - Statistical analysis of DNA relationships
- **Generation estimator** - Calculate genealogical distance
- **Genetic clustering** - Hierarchical and similarity-based clustering
- **Triangulation group identification** - Find shared match patterns

#### Narrative Memory System
- Store events as narrative memories with emotional significance
- Connect related memories to build narrative threads
- Query memories by type, tags, significance, or content
- Auto-tag memories based on content analysis
- Maintain contextual relationships between events

#### Governance Rituals
- Coordinate decision-making across multiple agents
- Implement council-based voting systems
- Execute structured rituals for coordination and review
- Track decision history and ritual executions
- Enable autonomous agent collaboration

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/isacjaco/SagaScout.git
cd SagaScout

# Install dependencies
pip install -r requirements.txt

# Install SagaScout
pip install -e .
```

## 📖 Quick Start

```python
from sagascout import Scout, Archivist, Oracle, Diplomat
from sagascout.utils import DNAAnalyzer, NarrativeMemory

# Create agents
scout = Scout(name="MyScout")
archivist = Archivist(name="MyArchivist")
oracle = Oracle(name="MyOracle")
diplomat = Diplomat(name="MyDiplomat")

# Analyze DNA matches
match_data = {
    "matches": [
        {"id": "m1", "name": "John Doe", "shared_cm": 850, "segments": 15}
    ],
    "threshold_cm": 20
}
results = scout.process(match_data)
print(f"Found {results['cluster_count']} clusters")

# Parse family tree
tree_data = {
    "action": "parse",
    "data": {
        "individuals": [
            {"id": "p1", "name": "Jane Smith", "birth_year": 1950}
        ],
        "relationships": []
    }
}
archivist.process(tree_data)

# Conduct multilingual research
research = {
    "action": "research",
    "query": "Smith family immigration",
    "languages": ["en", "es", "de"],
    "countries": ["US", "MX", "DE"]
}
results = oracle.process(research)

# Draft outreach message
message = {
    "action": "draft",
    "recipient": {"id": "m1", "name": "John Doe", "country": "US"},
    "purpose": "initial_contact",
    "language": "en"
}
draft = diplomat.process(message)
print(draft["draft"]["body"])
```

## 📚 Documentation

### Agent API Reference

#### Scout Agent

```python
scout = Scout(name="ScoutAgent", config={})

# Process DNA matches
results = scout.process({
    "matches": [...],
    "threshold_cm": 20
})

# Analyze individual match
analysis = scout.analyze_match(match_data)

# Get specific cluster
cluster = scout.get_cluster("1st_2nd_cousins")
```

#### Archivist Agent

```python
archivist = Archivist(name="ArchivistAgent", config={})

# Parse tree
archivist.process({"action": "parse", "data": {...}})

# Merge trees
archivist.process({"action": "merge", "data": {...}})

# Infer relationships
archivist.process({
    "action": "infer",
    "data": {"person1": "p1", "person2": "p2"}
})

# Query tree
archivist.process({
    "action": "query",
    "data": {"type": "ancestors", "person_id": "p1"}
})
```

#### Oracle Agent

```python
oracle = Oracle(name="OracleAgent", config={})

# Research
oracle.process({"action": "research", "query": "...", "languages": [...]})

# Extract document
oracle.process({"action": "extract", "document": {...}, "type": "birth_record"})

# Search archives
oracle.process({"action": "search_archives", "query": "...", "countries": [...]})

# Translate query
oracle.process({"action": "translate", "query": "...", "languages": [...]})
```

#### Diplomat Agent

```python
diplomat = Diplomat(name="DiplomatAgent", config={})

# Draft message
diplomat.process({"action": "draft", "recipient": {...}, "purpose": "..."})

# Send message
diplomat.process({"action": "send", "message": {...}})

# Respond to message
diplomat.process({"action": "respond", "original_message": {...}})

# Analyze culture
diplomat.process({"action": "analyze_culture", "country": "JP"})
```

### Utility Functions

```python
from sagascout.utils import DNAAnalyzer, NarrativeMemory, GovernanceRitual

# DNA Analysis
analyzer = DNAAnalyzer()
probabilities = analyzer.calculate_relationship_probability(850, 15)
generations = analyzer.estimate_generations(850)

# Narrative Memory
memory = NarrativeMemory()
mem_id = memory.store_memory("discovery", {...}, significance=0.8)
memories = memory.recall_memories(tags=["research"])

# Governance
governance = GovernanceRitual()
ritual_id = governance.create_ritual("Decision", "decision", [...], {...})
result = governance.execute_ritual(ritual_id, {...})
```

## 🎯 Use Cases

1. **DNA Match Analysis**: Automatically cluster and analyze DNA matches from services like AncestryDNA, 23andMe, or MyHeritage
2. **Family Tree Building**: Parse, merge, and maintain complex family trees with relationship inference
3. **International Research**: Conduct multilingual research across archives in multiple countries
4. **Cultural Outreach**: Draft culturally-appropriate messages to DNA matches worldwide
5. **Evidence Gathering**: Extract and organize information from historical documents
6. **Collaborative Research**: Coordinate multiple specialized agents for comprehensive genealogical projects

## 🛠️ Development

### Running Examples

```bash
# Run the basic usage examples
python examples/basic_usage.py
```

### Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest tests/
```

## 🌍 Supported Features

- **Languages**: 17+ languages including English, Spanish, French, German, Italian, Portuguese, Dutch, Swedish, Norwegian, Danish, Polish, Russian, Chinese, Japanese, Korean, Arabic, Hebrew
- **Archives**: Support for major genealogical databases including Ancestry.com, FamilySearch, MyHeritage, FindMyPast, and various national archives
- **DNA Platforms**: Compatible with DNA data formats from major testing services
- **Cultural Profiles**: Built-in cultural communication guidelines for US, UK, Japan, Germany, France, and more

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

SagaScout is part of a larger vision for autonomous genealogical research, combining:
- DNA analysis and clustering
- Family tree parsing and relationship inference
- Multilingual web research
- Document extraction and evidence gathering
- Cross-cultural communication
- Narrative-driven memory systems
- Agent governance and coordination

## 📞 Contact

For questions, issues, or collaboration opportunities, please open an issue on GitHub.

---

**SagaScout** - Connecting families across generations, borders, and cultures. 🌍🧬👨‍👩‍👧‍👦
