# Programming Knowledge Graph Generator

A tool to create a comprehensive knowledge graph of topics, concepts, and their relationships.

## Overview

This project fetches domain-specific data from multiple sources and combines them into a cohesive knowledge graph that can be used for:

- Learning path generation
- Visualizing relationships between concepts
- Educational content organization
- Research on evolution and relationships

## Features

- Retrieves domain-specific topics from Wikidata using SPARQL
- Enriches topics with Wikipedia content, summaries and categories
- Handles disambiguation pages and search intelligently
- Creates a preliminary graph structure with topics as nodes and relationships as edges
- Uses async and batching to be efficient
- Comprehensive error handling and logging
- Caches results in redis to avoid redundant API calls
- Stores topics in mongoDB for easy access and manipulation

## Installation

1. Make sure you have Python 3.12+ installed
2. Clone this repository
3. Install dependencies:

```bash
pip install uv
uv venv
source .venv/bin/activate
uv sync --reinstall
```

## Usage

Run the main script to generate the knowledge graph:

```bash
python -m src.main.py --limit 10 --domain programming
```

The output will be saved to the `output` directory with a timestamp in the filename.

## Data Structure

The generated knowledge graph JSON has the following structure:

```json
{
  "topics": [
    {
      "id": "Q2005",
      "title": "Python",
      "description": "high-level programming language",
      "topic_type": "programming_language",
      "properties": { ... },
      "references": ["Q80228", "Q28865", ...],
      "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
      "summary": "",
      "content": "",
      "content_for_embedding": ""
    }
  ],
  "edges": [
    {
      "source": "Q2005",
      "target": "Q80228"
    },
  ],
  "metadata": {
    "generated_at": "2023-05-20 12:34:56",
    "topic_count": 20,
    "edge_count": 45
  }
}
```

## Configuration

Add domain and queries in config.py and wikidata/queries.py.
The `config.py` file contains the main configuration for the project, including the domain and the SPARQL queries to be used.
