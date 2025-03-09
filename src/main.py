"""Main entry point for the learning path knowledge graph generator."""

import asyncio
import time
import argparse

from src.data_collection import get_and_save_from_wiki
from src.knowledge_graph import get_and_save_kg
from src.config import OUTPUT_DIR, DEFAULT_GRAPH_LIMIT, DOMAIN, DOMAIN_CONFIGS
from src.logger import get_logger

logger = get_logger()


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

        # Add timestamp and domain to output filename for versioning
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        timestamp_dir = OUTPUT_DIR / f"{timestamp}"
        timestamp_dir.mkdir(parents=True, exist_ok=True)

        # Fetch and enrich topics
        enriched_topics = await get_and_save_from_wiki(
            domain=domain, limit=limit, save_dir=timestamp_dir
        )

        # Generate knowledge graph data
        await get_and_save_kg(
            domain=domain, enriched_topics=enriched_topics, save_dir=timestamp_dir
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
