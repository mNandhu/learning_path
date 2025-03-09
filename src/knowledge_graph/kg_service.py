import json
import time

from src.logger import get_logger
from src.config import DOMAIN_CONFIGS
from .generate_kg import create_knowledge_graph_data
from .visualize_graph import generate_graphml_and_save_as_html

logger = get_logger(__name__)


async def get_and_save_kg(domain, enriched_topics: list, save_dir: str) -> dict:
    logger.info(
        f"Generating knowledge graph for domain: {DOMAIN_CONFIGS[domain]['name']} (async mode)"
    )
    output_file = save_dir / f"{domain}_knowledge_graph.json"
    # Create knowledge graph data
    knowledge_graph_data = create_knowledge_graph_data(enriched_topics)

    # Add metadata to the output
    knowledge_graph_data["metadata"] = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "domain": domain,
        "domain_name": DOMAIN_CONFIGS[domain]["name"],
        "topic_count": len(enriched_topics),
        "edge_count": len(knowledge_graph_data["edges"]),
    }

    # Save to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(knowledge_graph_data, f, ensure_ascii=False, indent=2)

    # Generate and save knowledge graph visualization
    generate_graphml_and_save_as_html(knowledge_graph_data, save_dir=save_dir)

    logger.info(
        f"Successfully saved knowledge graph with {len(enriched_topics)} topics and "
        f"{len(knowledge_graph_data['edges'])} edges to {output_file}"
    )
