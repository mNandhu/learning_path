from .wikidata.sparql import get_topics_from_wikidata
from .wikipedia_.api import enrich_with_wikipedia
from src.logger import logger
import json


async def get_data_from_wiki(domain: str, limit: int) -> list:
    """
    Fetch and enrich topics from Wikidata and Wikipedia.
    Args:
        domain: The knowledge domain to use (e.g., "programming", "mathematics")
        limit: Maximum number of topics to fetch
    Returns:
        List of enriched topics
    """
    # Fetch topics from Wikidata using async
    topics = await get_topics_from_wikidata(domain=domain, limit=limit)
    if not topics:
        logger.error(f"Failed to retrieve {domain} topics from Wikidata")
        return

    logger.info(f"Successfully retrieved {len(topics)} {domain} topics from Wikidata")

    # Enrich with Wikipedia data using async
    enriched_topics = await enrich_with_wikipedia(topics, domain=domain)
    if not enriched_topics:
        logger.error(f"Failed to enrich {domain} topics with Wikipedia data")
        return
    logger.info(
        f"Successfully enriched {len(enriched_topics)} topics with Wikipedia data"
    )
    return enriched_topics


async def get_and_save_from_wiki(domain: str, limit: int, save_dir: str) -> list:
    """
    Fetch and enrich topics from Wikidata and Wikipedia.
    Args:
        domain: The knowledge domain to use (e.g., "programming", "mathematics")
        limit: Maximum number of topics to fetch
        dir: Directory to save the enriched topics
    Returns:
        List of enriched topics
    """
    enriched_output_file = save_dir / f"enriched_{domain}_topics.json"
    enriched_topics = await get_data_from_wiki(domain=domain, limit=limit)
    if not enriched_topics:
        logger.error(f"Failed to enrich {domain} topics with Wikipedia data")
        return []
    # Save enriched topics to JSON file
    with open(enriched_output_file, "w", encoding="utf-8") as f:
        json.dump(enriched_topics, f, ensure_ascii=False, indent=2)
    logger.info(f"Successfully saved enriched topics to {enriched_output_file}")
    return enriched_topics
