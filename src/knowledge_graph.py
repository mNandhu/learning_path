from logger import logger
import re


def create_knowledge_graph_data(topics):
    """Structure the data for knowledge graph creation."""
    logger.info("Creating knowledge graph data structure...")

    # Process topics to add reference links and prepare for embedding
    for topic in topics:
        # Extract all related topics from properties
        references = []

        # Look through all properties for Wikidata IDs
        for prop_name, prop_values in topic["properties"].items():
            for value in prop_values:
                if "id" in value and value["id"].startswith("Q"):
                    references.append(value["id"])

        # Add references to topic
        topic["references"] = list(set(references))

        # Clean up content for embedding generation
        if "content" in topic:
            # Remove citations and normalize whitespace
            cleaned_content = re.sub(r"\[\d+\]", "", topic["content"])
            cleaned_content = re.sub(r"\s+", " ", cleaned_content)
            topic["content_for_embedding"] = cleaned_content.strip()

    # Create edges data structure
    edges = []
    for topic in topics:
        topic_id = topic["id"]
        for ref_id in topic["references"]:
            # Check if the referenced topic is in our dataset
            if any(t["id"] == ref_id for t in topics):
                edges.append(
                    {
                        "source": topic_id,
                        "target": ref_id,
                        # Later weights can be added using embeddings
                    }
                )

    return {"topics": topics, "edges": edges}
