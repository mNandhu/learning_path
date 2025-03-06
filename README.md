# Programming Knowledge Graph Generator

A tool to create a comprehensive knowledge graph of programming topics, concepts, languages, and their relationships. The graph is built by combining structured data from Wikidata with rich content from Wikipedia.

## Overview

This project fetches programming-related data from multiple sources and combines them into a cohesive knowledge graph that can be used for:

- Learning path generation
- Visualizing relationships between programming concepts
- Educational content organization
- Research on programming language evolution and relationships

## Features

- Retrieves programming topics from Wikidata using SPARQL
- Enriches topics with Wikipedia content, summaries and categories
- Handles disambiguation pages and search intelligently
- Creates a graph structure with topics as nodes and relationships as edges
- Implements proper rate limiting to respect API usage policies
- Comprehensive error handling and logging

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
python src/main.py
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
      "summary": "...",
      "content": "...",
      "content_for_embedding": "..."
    }
    // More topics...
  ],
  "edges": [
    {
      "source": "Q2005",
      "target": "Q80228"
    }
    // More edges...
  ],
  "metadata": {
    "generated_at": "2023-05-20 12:34:56",
    "topic_count": 20,
    "edge_count": 45
  }
}
```

## Configuration

- Modify `sparql.py` to adjust the SPARQL queries for retrieving specific programming topics
- Adjust the rate limiting parameters in both `wikipedia.py` and `sparql.py` if needed
- Change the output format in `main.py` if needed

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
