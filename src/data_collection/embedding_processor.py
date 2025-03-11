"""Process topics from MongoDB to generate and store embeddings."""

import asyncio
from typing import List, Dict, Any, Optional

from src.logger import get_logger
from src.database.mongo import get_topics_from_mongo, store_topics_in_mongo
from src.embeddings.service import process_topics_batch_async

logger = get_logger(__name__)


async def process_topics_to_embeddings(
    domain: str,
    collection_name: Optional[str] = None,
    limit: int = 100,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    topics=None,
) -> List[Dict[str, Any]]:
    """Process topics from MongoDB, generate embeddings, and store in ChromaDB.

    Args:
        domain: The domain of topics to process (e.g., "programming")
        collection_name: Name for the ChromaDB collection (defaults to f"{domain}_embeddings")
        limit: Maximum number of topics to process
        chunk_size: Size of content chunks for embeddings
        chunk_overlap: Overlap between chunks

    Returns:
        List of processed topics with embedding references
    """
    # Set default collection name based on domain if not provided
    if not collection_name:
        collection_name = f"{domain}_embeddings"

    # Get topics from MongoDB
    logger.info(
        f"Retrieving {limit} {domain} topics from MongoDB for embedding generation"
    )
    if topics is None:
        topics = await get_topics_from_mongo(domain=domain, limit=limit)

        if not topics:
            logger.warning(f"No topics found in MongoDB for domain '{domain}'")
            return []

    logger.info(f"Processing {len(topics)} topics for embedding generation")

    # Process topics to generate and store embeddings
    # Use the async version directly since we're    n async context
    processed_topics = await process_topics_batch_async(
        topics=topics,
        collection_name=collection_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Write to a file
    import json
    from bson import ObjectId

    def convert_objectid_to_str(obj):
        if isinstance(obj, dict):
            return {k: convert_objectid_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_objectid_to_str(elem) for elem in obj]
        elif hasattr(obj, "oid"):  # Check if it's an ObjectId-like object
            return str(obj.oid)  # Access the 'oid' attribute and convert to string
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj

    processed_topics_serializable = convert_objectid_to_str(processed_topics)

    with open(f"{collection_name}.json", "w") as f:
        json.dump(processed_topics_serializable, f)

    # Update topics in MongoDB with embedding references
    logger.info(
        f"Updating {len(processed_topics)} topics in MongoDB with embedding references"
    )
    success = await store_topics_in_mongo(topics=processed_topics, domain=domain)

    if success:
        logger.info("Successfully updated topics with embedding references in MongoDB")
    else:
        logger.error("Failed to update topics with embedding references in MongoDB")

    return processed_topics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process topics to generate embeddings"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="programming",
        help="Domain to process (e.g., programming, mathematics)",
    )
    parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of topics to process"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="ChromaDB collection name (defaults to {domain}_embeddings)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Size of content chunks for embeddings",
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=50, help="Overlap between chunks"
    )

    args = parser.parse_args()

    asyncio.run(
        process_topics_to_embeddings(
            domain=args.domain,
            collection_name=args.collection,
            limit=args.limit,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    )
