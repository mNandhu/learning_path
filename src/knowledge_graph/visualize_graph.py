import networkx as nx
from pyvis.network import Network
import random
import json
from pathlib import Path
import os
import time
from src.config import DOMAIN_COLORS, DOMAIN, TOPIC_TYPE_COLORS
from src.logger import logger


def _convert_to_graphml(knowledge_graph_data):
    """Convert knowledge graph data to GraphML format."""
    logger.info("Converting knowledge graph data to GraphML format...")

    # Get domain from metadata if available, otherwise use default
    domain = knowledge_graph_data.get("metadata", {}).get("domain", DOMAIN)
    # Get the color scheme for the domain
    color_scheme = DOMAIN_COLORS.get(domain, DOMAIN_COLORS[DOMAIN])

    # Initialize GraphML structure
    graphml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    graphml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'

    # Define attribute keys
    graphml += '  <key id="label" for="node" attr.name="label" attr.type="string"/>\n'
    graphml += '  <key id="description" for="node" attr.name="description" attr.type="string"/>\n'
    graphml += '  <key id="topic_type" for="node" attr.name="topic_type" attr.type="string"/>\n'
    graphml += '  <key id="color" for="node" attr.name="color" attr.type="string"/>\n'
    graphml += (
        '  <key id="edge_type" for="edge" attr.name="type" attr.type="string"/>\n'
    )
    graphml += '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>\n'

    graphml += '  <graph id="G" edgedefault="undirected">\n'

    # Add nodes with attributes
    for topic in knowledge_graph_data["topics"]:
        # Generate a color based on topic type
        topic_type = topic.get("topic_type", "unknown").lower()
        color = _get_color_for_topic_type(topic_type, color_scheme)

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
        edge_type = edge.get("type", "unknown")
        weight = edge.get("weight", 1)
        graphml += f'    <edge source="{edge["source"]}" target="{edge["target"]}">\n'
        graphml += f'      <data key="edge_type">{edge_type}</data>\n'
        graphml += f'      <data key="weight">{weight}</data>\n'
        graphml += "    </edge>\n"

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


def _get_color_for_topic_type(topic_type, color_scheme=None):
    """Return a color hex code based on topic type for consistent coloring.

    Args:
        topic_type: The topic type to get a color for
        color_scheme: Optional color scheme dictionary to use

    Returns:
        A hex color code for the topic type
    """
    if color_scheme is None:
        color_scheme = TOPIC_TYPE_COLORS

    # Convert to lowercase and strip any extra whitespace
    if isinstance(topic_type, str):
        topic_type = topic_type.lower().strip()

    return color_scheme.get(topic_type, color_scheme.get("unknown", "#cccccc"))


def _save_graphml(graphml, filename):
    """Save GraphML data to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(graphml)
    logger.info(f"GraphML data saved to {filename}")


def _create_networkx_graph(knowledge_graph_data):
    """Create a NetworkX graph from knowledge graph data."""
    G = nx.Graph()

    # Get domain from metadata if available, otherwise use default
    domain = knowledge_graph_data.get("metadata", {}).get("domain", DOMAIN)
    # Get the color scheme for the domain
    color_scheme = DOMAIN_COLORS.get(domain, DOMAIN_COLORS[DOMAIN])

    # Add nodes with attributes
    for topic in knowledge_graph_data["topics"]:
        topic_type = topic.get("topic_type", "unknown").lower()
        node_attrs = {
            "label": topic["title"],
            "description": topic.get("description", ""),
            "topic_type": topic_type,
            "color": _get_color_for_topic_type(topic_type, color_scheme),
            "title": f"{topic['title']}<br>{topic.get('description', '')}",  # HTML tooltip
        }
        G.add_node(topic["id"], **node_attrs)

    # Add edges with attributes
    for edge in knowledge_graph_data["edges"]:
        edge_type = edge.get("type", "unknown")
        weight = edge.get("weight", 1)
        G.add_edge(
            edge["source"],
            edge["target"],
            type=edge_type,
            weight=weight,
            title=f"Type: {edge_type}",  # HTML tooltip
        )

    return G


def _save_as_html(G, output_path):
    """Visualize the knowledge graph using Pyvis."""
    # Set random seed for reproducibility
    random.seed(42)

    # Create a Pyvis network
    net = Network(height="800px", width="100%", notebook=False, directed=False)

    # Use physics for better graph layout
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250)

    # Add nodes and edges from NetworkX graph
    net.from_nx(G)

    # Set options for better visualization - show tooltips and use node colors
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
          "size": 14,
          "face": "Tahoma",
          "color": "#333333"
        },
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "scaling": {
          "min": 20,
          "max": 30
        },
        "shadow": true
      },
      "edges": {
        "color": {
          "inherit": false,
          "opacity": 0.7
        },
        "smooth": {
          "enabled": true,
          "type": "continuous"
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "shadow": true
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "hideEdgesOnDrag": true
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
    # Extract the base name of the input JSON file
    base_name = Path(
        knowledge_graph_data.get("metadata", {}).get("filename", "knowledge_graph")
    ).stem

    timestamp_dir = knowledge_graph_data.get("metadata", {}).get(
        "timestamp", time.strftime("%Y%m%d_%H%M%S")
    )
    timestamp_path = output_dir / timestamp_dir
    timestamp_path.mkdir(exist_ok=True)

    graphml_file = timestamp_path / f"{base_name}.graphml"
    html_file = timestamp_path / f"{base_name}.html"

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
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate visualizations for a knowledge graph"
    )
    parser.add_argument(
        "--file", type=str, help="Path to the knowledge graph JSON file"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=DOMAIN,
        choices=list(DOMAIN_COLORS.keys()),
        help=f"Domain to use for visualization colors (default: {DOMAIN})",
    )

    args = parser.parse_args()

    # Use specified file or find the latest
    if args.file:
        input_file = args.file
    else:
        output_dir = Path("output")
        json_files = list(output_dir.glob("*_knowledge_graph_*.json"))
        if not json_files:
            print("No knowledge graph files found. Please run main.py first.")
            sys.exit(1)
        input_file = str(max(json_files, key=os.path.getctime))
        print(f"Using the most recent file: {input_file}")

    # Load and process the file
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

        # Override domain if specified and not already in metadata
        if args.domain and "metadata" not in data:
            data["metadata"] = {"domain": args.domain}
        elif args.domain and "domain" not in data["metadata"]:
            data["metadata"]["domain"] = args.domain

        html_path = generate_graphml_and_save_as_html(data)
        print(f"Knowledge graph visualization created at {html_path}")
