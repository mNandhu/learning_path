"""Main entry point for the learning path knowledge graph generator."""

import asyncio
import json
import time
import argparse

from src.wikidata.sparql import get_topics_from_wikidata
from src.wikipedia_.api import enrich_with_wikipedia
from src.knowledge_graph.knowledge_graph import create_knowledge_graph_data
from src.knowledge_graph.visualize_graph import generate_graphml_and_save_as_html
from src.config import OUTPUT_DIR, DEFAULT_GRAPH_LIMIT, DOMAIN
from src.wikidata.queries import DOMAIN_CONFIGS
from src.logger import logger


async def main(domain: str = DOMAIN, limit: int = DEFAULT_GRAPH_LIMIT) -> None:
    """Async main function to generate the domain knowledge graph.

    Args:
        domain: The knowledge domain to use (e.g., "programming", "mathematics")
        limit: Maximum number of topics to fetch
    """
    try:
        # Validate domain
        if domain not in DOMAIN_CONFIGS:
            logger.error(
                f"Unknown domain: {domain}. Available domains: {list(DOMAIN_CONFIGS.keys())}"
            )
            logger.info(f"Falling back to default domain: {DOMAIN}")
            domain = DOMAIN

        logger.info(
            f"Generating knowledge graph for domain: {DOMAIN_CONFIGS[domain]['name']} (async mode)"
        )

        # Create output directory
        OUTPUT_DIR.mkdir(exist_ok=True)

        # Add timestamp and domain to output filename for versioning
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        timestamp_dir = OUTPUT_DIR / f"{timestamp}"
        timestamp_dir.mkdir(parents=True, exist_ok=True)
        output_file = timestamp_dir / f"{domain}_knowledge_graph.json"
        enriched_output_file = timestamp_dir / f"enriched_{domain}_topics.json"

        # Get topics from Wikidata for the specified domain using async
        topics = await get_topics_from_wikidata(domain=domain, limit=limit)
        if not topics:
            logger.error(f"Failed to retrieve {domain} topics from Wikidata")
            return

        logger.info(
            f"Successfully retrieved {len(topics)} {domain} topics from Wikidata"
        )

        # Enrich with Wikipedia data using async
        enriched_topics = await enrich_with_wikipedia(topics, domain=domain)

        # Save enriched topics to JSON file
        with open(enriched_output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_topics, f, ensure_ascii=False, indent=2)

        logger.info(f"Successfully saved enriched topics to {enriched_output_file}")
        logger.info(f"Successfully enriched {len(topics)} topics with Wikipedia data")

        # Create knowledge graph data
        knowledge_graph_data = create_knowledge_graph_data(enriched_topics)

        # Add metadata to the output
        knowledge_graph_data["metadata"] = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "domain": domain,
            "domain_name": DOMAIN_CONFIGS[domain]["name"],
            "topic_count": len(topics),
            "edge_count": len(knowledge_graph_data["edges"]),
            "filename": output_file.name,
            "timestamp": timestamp,
        }

        # Save to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_graph_data, f, ensure_ascii=False, indent=2)

        # Generate and save knowledge graph visualization
        generate_graphml_and_save_as_html(knowledge_graph_data)

        logger.info(
            f"Successfully saved knowledge graph with {len(topics)} topics and "
            f"{len(knowledge_graph_data['edges'])} edges to {output_file}"
        )
    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # Add command line argument support for domain selection
    parser = argparse.ArgumentParser(
        description="Generate a knowledge graph for a specific domain"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=DOMAIN,
        choices=list(DOMAIN_CONFIGS.keys()),
        help=f"Knowledge domain to use (default: {DOMAIN})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_GRAPH_LIMIT,
        help=f"Maximum number of topics to fetch (default: {DEFAULT_GRAPH_LIMIT})",
    )

    args = parser.parse_args()
    asyncio.run(main(domain=args.domain, limit=args.limit))
