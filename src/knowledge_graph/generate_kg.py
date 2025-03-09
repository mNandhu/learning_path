from src.logger import get_logger
import re
from typing import Dict, List, Any, Set
import json

logger = get_logger(__name__)


def create_knowledge_graph_data(topics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Structure the data for knowledge graph creation.

    Args:
        topics: List of topic dictionaries with properties and content

    Returns:
        Dictionary containing topics and edges for knowledge graph creation
    """
    logger.info("Creating knowledge graph data structure...")

    # First, create an ID lookup for faster reference checking
    topic_ids = {topic["id"]: topic for topic in topics}

    # Process topics to add reference links and prepare for embedding
    for topic in topics:
        # Extract all related topics from properties
        references: Set[str] = set()

        # Look through all properties for Wikidata IDs
        for prop_name, prop_values in topic["properties"].items():
            if isinstance(prop_values, str):
                # If the property was stored as a string (legacy format), try to parse it
                try:
                    prop_values = json.loads(prop_values)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not parse property {prop_name} for topic {topic['id']}"
                    )
                    continue

            # Handle both list and non-list property formats
            if isinstance(prop_values, list):
                for value in prop_values:
                    # Handle both dictionary values and string values
                    if (
                        isinstance(value, dict)
                        and "id" in value
                        and value["id"].startswith("Q")
                    ):
                        references.add(value["id"])
                    elif isinstance(value, str) and value.startswith("Q"):
                        references.add(value)
            elif (
                isinstance(prop_values, dict)
                and "id" in prop_values
                and prop_values["id"].startswith("Q")
            ):
                references.add(prop_values["id"])

        # Add references to topic
        topic["references"] = list(references)

        # Clean up content for embedding generation
        if "content" in topic:
            # Remove citations and normalize whitespace
            cleaned_content = re.sub(r"\[\d+]", "", topic["content"])
            cleaned_content = re.sub(r"\s+", " ", cleaned_content)
            topic["content_for_embedding"] = cleaned_content.strip()

    # Create edges data structure
    edges: List[Dict[str, Any]] = []

    # Set to track already created edges to avoid duplicates
    edge_tracker = set()

    # First pass: Create edges based on direct references
    for topic in topics:
        topic_id = topic["id"]
        for ref_id in topic["references"]:
            # Check if the referenced topic is in our dataset
            if ref_id in topic_ids:
                # Create bidirectional edge
                edge_key = tuple(sorted([topic_id, ref_id]))
                if edge_key not in edge_tracker:
                    edges.append(
                        {
                            "source": topic_id,
                            "target": ref_id,
                            "weight": 1,
                            "type": "reference",
                        }
                    )
                    edge_tracker.add(edge_key)

    # Second pass: Add edges based on shared properties
    # This helps connect more topics, especially when direct references are sparse
    for i, topic1 in enumerate(topics):
        for topic2 in topics[i + 1 :]:
            # Skip if already connected
            edge_key = tuple(sorted([topic1["id"], topic2["id"]]))
            if edge_key in edge_tracker:
                continue

            # Check if they share the same type
            if topic1.get("topic_type") == topic2.get("topic_type") and topic1.get(
                "topic_type"
            ):
                edges.append(
                    {
                        "source": topic1["id"],
                        "target": topic2["id"],
                        "weight": 0.5,
                        "type": "same_type",
                    }
                )
                edge_tracker.add(edge_key)
                continue

            # Check for other commonalities that could justify a connection
            # For example, check if they share categories from Wikipedia
            if "categories" in topic1 and "categories" in topic2:
                shared_categories = set(topic1["categories"]) & set(
                    topic2["categories"]
                )
                if shared_categories:
                    edges.append(
                        {
                            "source": topic1["id"],
                            "target": topic2["id"],
                            "weight": 0.3,
                            "type": "shared_category",
                        }
                    )
                    edge_tracker.add(edge_key)

    logger.info(
        f"Created knowledge graph with {len(topics)} nodes and {len(edges)} edges"
    )
    return {"topics": topics, "edges": edges}
