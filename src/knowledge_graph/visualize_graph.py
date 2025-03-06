import networkx as nx
from pyvis.network import Network
import random
from logger import logger
import json
from pathlib import Path
import os


def _convert_to_graphml(knowledge_graph_data):
    """Convert knowledge graph data to GraphML format."""
    logger.info("Converting knowledge graph data to GraphML format...")

    # Initialize GraphML structure
    graphml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    graphml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'

    # Define attribute keys
    graphml += '  <key id="label" for="node" attr.name="label" attr.type="string"/>\n'
    graphml += '  <key id="description" for="node" attr.name="description" attr.type="string"/>\n'
    graphml += '  <key id="topic_type" for="node" attr.name="topic_type" attr.type="string"/>\n'
    graphml += '  <key id="color" for="node" attr.name="color" attr.type="string"/>\n'

    graphml += '  <graph id="G" edgedefault="undirected">\n'

    # Add nodes with attributes
    for topic in knowledge_graph_data["topics"]:
        # Generate a color based on topic type
        topic_type = topic.get("topic_type", "unknown")
        color = _get_color_for_topic_type(topic_type)

        graphml += f'    <node id="{topic["id"]}">\n'
        graphml += f'      <data key="label">{_escape_xml(topic["title"])}</data>\n'

        if "description" in topic and topic["description"]:
            graphml += f'      <data key="description">{_escape_xml(topic["description"])}</data>\n'

        if "topic_type" in topic and topic["topic_type"]:
            graphml += f'      <data key="topic_type">{_escape_xml(topic["topic_type"])}</data>\n'

        graphml += f'      <data key="color">{color}</data>\n'
        graphml += "    </node>\n"

    # Add edges
    for edge in knowledge_graph_data["edges"]:
        graphml += f'    <edge source="{edge["source"]}" target="{edge["target"]}"/>\n'

    graphml += "  </graph>\n"
    graphml += "</graphml>"

    return graphml


def _escape_xml(text):
    """Escape special characters for XML."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _get_color_for_topic_type(topic_type):
    """Return a color hex code based on topic type for consistent coloring."""
    colors = {
        "programming_language": "#66c2a5",
        "programming_paradigm": "#fc8d62",
        "programming_concept": "#8da0cb",
        "software_framework": "#e78ac3",
        "software_development": "#a6d854",
    }
    return colors.get(topic_type.lower(), "#cccccc")  # Default gray for unknown types


def _save_graphml(graphml, filename):
    """Save GraphML data to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(graphml)
    logger.info(f"GraphML data saved to {filename}")


def _create_networkx_graph(knowledge_graph_data):
    """Create a NetworkX graph from knowledge graph data."""
    G = nx.Graph()

    # Add nodes with attributes
    for topic in knowledge_graph_data["topics"]:
        node_attrs = {
            "label": topic["title"],
            "description": topic.get("description", ""),
            "topic_type": topic.get("topic_type", "unknown"),
            "color": _get_color_for_topic_type(topic.get("topic_type", "unknown")),
        }
        G.add_node(topic["id"], **node_attrs)

    # Add edges
    for edge in knowledge_graph_data["edges"]:
        G.add_edge(edge["source"], edge["target"])

    return G


def _save_as_html(G, output_path):
    """Visualize the knowledge graph using Pyvis."""
    # Set random seed for reproducibility
    random.seed(42)

    # Create a Pyvis network
    net = Network(height="800px", width="100%", notebook=False, directed=False)
    net.from_nx(G)

    # Set options for better visualization
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 150
        }
      },
      "nodes": {
        "font": {
          "size": 14
        }
      },
      "edges": {
        "color": {
          "opacity": 0.7
        },
        "smooth": {
          "enabled": true,
          "type": "continuous"
        }
      }
    }
    """)

    # Save the visualization to HTML
    net.write_html(output_path, notebook=False)
    logger.info(f"Interactive visualization saved to {output_path}")


def generate_graphml_and_save_as_html(knowledge_graph_data: dict, output_dir="output"):
    """Generate and save the knowledge graph as GraphML and HTML files."""
    logger.info("Generating and saving knowledge graph visualizations...")

    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Set filenames
    graphml_file = output_dir / "knowledge_graph.graphml"
    html_file = output_dir / "knowledge_graph.html"

    # Convert to GraphML
    graphml = _convert_to_graphml(knowledge_graph_data)

    # Save GraphML
    _save_graphml(graphml, graphml_file)

    # Create NetworkX graph directly from data (more reliable than parsing GraphML)
    G = _create_networkx_graph(knowledge_graph_data)

    # Save as HTML visualization
    _save_as_html(G, str(html_file))

    return str(html_file)


if __name__ == "__main__":
    import json
    import sys

    # Use the latest JSON file if no specific file is provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        output_dir = Path("output")
        json_files = list(output_dir.glob("programming_knowledge_graph_*.json"))
        if not json_files:
            print("No knowledge graph files found. Please run main.py first.")
            sys.exit(1)
        input_file = str(max(json_files, key=os.path.getctime))
        print(f"Using the most recent file: {input_file}")

    with open(input_file, encoding="utf-8") as f:
        html_path = generate_graphml_and_save_as_html(json.load(f))
        print(f"Knowledge graph visualization created at {html_path}")
