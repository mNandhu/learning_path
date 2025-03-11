"""Main entry point for the learning path knowledge graph generator."""

import asyncio
import time
import argparse

from src.data_collection import get_and_save_from_wiki
from src.data_collection.embedding_processor import process_topics_to_embeddings

# from src.knowledge_graph import get_and_save_kg
from src.config import OUTPUT_DIR, DEFAULT_GRAPH_LIMIT, DOMAIN, DOMAIN_CONFIGS
from src.logger import get_logger

logger = get_logger()


async def main(
    domain: str = DOMAIN,
    limit: int = DEFAULT_GRAPH_LIMIT,
    process_embeddings: bool = False,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> None:
    """Async main function to generate the domain knowledge graph.

    Args:
        domain: The knowledge domain to use (e.g., "programming", "mathematics")
        limit: Maximum number of topics to fetch
        process_embeddings: Whether to process and store embeddings
        chunk_size: Size of content chunks for embeddings
        chunk_overlap: Overlap between chunks
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
            domain=domain,
            limit=limit,
            save_dir=timestamp_dir,
            save_to_mongo=not (process_embeddings),
        )

        # Process embeddings if requested
        if process_embeddings:
            logger.info("Processing embeddings for the enriched topics")
            await process_topics_to_embeddings(
                domain=domain,
                topics=enriched_topics,
                limit=limit,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        # Generate knowledge graph data
        # await get_and_save_kg(
        #     domain=domain, enriched_topics=enriched_topics, save_dir=timestamp_dir
        # )

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
    parser.add_argument(
        "--process-embeddings",
        action="store_true",
        help="Process and store embeddings for the topics",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Size of content chunks for embeddings (default: 500)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks for embeddings (default: 50)",
    )

    args = parser.parse_args()
    asyncio.run(
        main(
            domain=args.domain,
            limit=args.limit,
            process_embeddings=args.process_embeddings,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )
