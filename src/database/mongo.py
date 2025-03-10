"""MongoDB client integration for async operations."""

from motor.motor_asyncio import AsyncIOMotorClient
from src.config import MONGO_URI, MONGO_DB, MONGO_COLLECTION
from typing import Dict, Any, List
from src.logger import get_logger

logger = get_logger(__name__)


async def get_mongo_client():
    """Get asynchronous MongoDB client using motor."""
    client = AsyncIOMotorClient(MONGO_URI)
    return client[MONGO_DB]


async def store_topics_in_mongo(topics: List[Dict[str, Any]], domain: str) -> bool:
    """Store enriched topics in MongoDB with domain and timestamp.

    Args:
        topics: List of topic dictionaries
        domain: The domain of topics (e.g., "programming")

    Returns:
        True if operation was successful
    """
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        # Bulk insert or update topics
        if topics:
            # Use topic['id'] as the key for upsert operations
            operations = []
            for topic in topics:
                result = await collection.update_one(
                    {"id": topic["id"], "domain": domain}, {"$set": topic}, upsert=True
                )
                operations.append(result)

            logger.info(f"Successfully stored {len(topics)} topics in MongoDB")
            return True

        return False
    except Exception as e:
        logger.error(f"Error storing topics in MongoDB: {str(e)}")
        return False


async def get_topics_from_mongo(
    domain: str, limit: int = 100, filter_criteria: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Retrieve topics from MongoDB by domain.

    Args:
        domain: The domain of topics to retrieve
        limit: Maximum number of topics to retrieve
        filter_criteria: Additional filter criteria (e.g., {"has_embeddings": True})

    Returns:
        List of topic dictionaries
    """
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        # Build query
        query = {"domain": domain}
        if filter_criteria:
            query.update(filter_criteria)

        cursor = collection.find(query).limit(limit)
        topics = await cursor.to_list(length=limit)

        logger.info(f"Retrieved {len(topics)} topics from MongoDB")
        return topics
    except Exception as e:
        logger.error(f"Error retrieving topics from MongoDB: {str(e)}")
        return []
