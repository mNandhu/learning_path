"""Asynchronous Wikidata SPARQL API client."""

import asyncio
import aiohttp
import json
from src.logger import get_logger
from src.database.redis import get_redis_client
from typing import List, Dict, Any, Optional
from src.config import (
    WIKIDATA_ENDPOINT,
    WIKIDATA_USER_AGENT,
    DOMAIN,
    BATCH_SIZE,
)
from .queries import get_topic_query, get_properties_query, DOMAIN_CONFIGS

logger = get_logger(__name__)


async def get_topics_from_wikidata(
    domain: str = DOMAIN, limit: int = 20
) -> List[Dict[str, Any]]:
    """Fetch domain-specific topics from Wikidata using SPARQL (async).

    Args:
        domain: Domain to fetch topics for (e.g., "programming", "mathematics")
        limit: Maximum number of topics to retrieve

    Returns:
        List of topics with their properties
    """
    logger.info(f"Fetching {domain} topics from Wikidata...")

    # Verify domain is supported
    if domain not in DOMAIN_CONFIGS:
        logger.error(f"Unsupported domain: {domain}. Using default domain: {DOMAIN}")
        domain = DOMAIN

    # Get the query for the specified domain
    query = get_topic_query(domain, limit)

    try:
        # Execute SPARQL query using aiohttp directly
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WIKIDATA_ENDPOINT,
                headers={
                    "User-Agent": WIKIDATA_USER_AGENT,
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"query": query},
            ) as response:
                if response.status != 200:
                    logger.error(f"SPARQL query failed with status {response.status}")
                    return []

                results = await response.json()
    except Exception as e:
        logger.error(f"SPARQL query failed: {str(e)}")
        return []

    # Process results into structured format
    topics: Dict[str, Dict[str, Any]] = {}
    for result in results["results"]["bindings"]:
        topic_id = result["topic"]["value"].split("/")[-1]

        if topic_id not in topics:
            # Extract topic type directly from the binding
            topic_type = ""
            if "topicType" in result:
                topic_type = result["topicType"]["value"]

            topics[topic_id] = {
                "id": topic_id,
                "title": result["topicLabel"]["value"],
                "wikidata_url": result["topic"]["value"],
                "description": result.get("description", {}).get("value", ""),
                "topic_type": topic_type,
                "properties": {},
            }

    # Process topics in batches
    topic_ids = list(topics.keys())
    redis_client = get_redis_client()

    # Divide topics into batches
    batches = [
        topic_ids[i : i + BATCH_SIZE] for i in range(0, len(topic_ids), BATCH_SIZE)
    ]

    for batch in batches:
        # Process each batch concurrently with asyncio.gather
        await asyncio.gather(
            *[
                get_topic_properties(topic_id, topics[topic_id], domain, redis_client)
                for topic_id in batch
            ]
        )

        # Sleep to avoid overwhelming the server
        await asyncio.sleep(0.5)

    return list(topics.values())


async def get_topic_properties(
    topic_id: str,
    topic: Dict[str, Any],
    domain: str,
    redis_client: Optional[Any] = None,
) -> bool:
    """Get detailed properties for a specific topic (async).

    Args:
        topic_id: The Wikidata entity ID
        topic: The topic dictionary to update
        domain: The domain being processed
        redis_client: Redis client for caching

    Returns:
        True if successful, False otherwise
    """
    # Check cache first if redis client is provided
    if redis_client:
        cache_key = f"wikidata:{domain}:{topic_id}"
        cached_properties = redis_client.hgetall(cache_key)

        if cached_properties:
            # Retrieve properties from cache
            properties = {}
            for k, v in cached_properties.items():
                key = k.decode("utf-8") if isinstance(k, bytes) else k
                try:
                    value = json.loads(v.decode("utf-8") if isinstance(v, bytes) else v)
                    properties[key] = value
                except (json.JSONDecodeError, TypeError):
                    # Fallback for old format
                    properties[key] = v.decode("utf-8") if isinstance(v, bytes) else v

            topic["properties"] = properties
            return True

    # If not in cache or no redis client, fetch from Wikidata
    query = get_properties_query(topic_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WIKIDATA_ENDPOINT,
                headers={
                    "User-Agent": WIKIDATA_USER_AGENT,
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"query": query},
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Properties query failed with status {response.status} for {topic_id}"
                    )
                    return False

                results = await response.json()

        # Process the results into structured format
        for result in results["results"]["bindings"]:
            property_label = result["propertyLabel"]["value"]
            value_url = result["value"]["value"]
            value_label = result["valueLabel"]["value"]

            # Extract Wikidata ID if it's an entity
            value_id = None
            if "wikidata.org/entity/" in value_url:
                value_id = value_url.split("/")[-1]

            # Initialize property group if it doesn't exist
            if property_label not in topic["properties"]:
                topic["properties"][property_label] = []

            # Create value object with label, URL and ID
            value_object = {"label": value_label, "url": value_url}

            if value_id:
                value_object["id"] = value_id

            # Add if not already present
            if not any(
                v.get("label") == value_label
                for v in topic["properties"][property_label]
            ):
                topic["properties"][property_label].append(value_object)

        # Cache properties if redis client is provided
        if redis_client:
            cache_key = f"wikidata:{domain}:{topic_id}"
            cache_data = {}
            for key, value in topic["properties"].items():
                cache_data[key] = json.dumps(value)
            redis_client.hset(cache_key, mapping=cache_data)

        return True

    except Exception as e:
        logger.error(f"Error fetching properties for {topic_id}: {str(e)}")
        return False
