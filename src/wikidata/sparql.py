from SPARQLWrapper import SPARQLWrapper, JSON
import time
from tqdm import tqdm
from src.logger import logger
from src.database.redis import get_redis_client
from typing import List, Dict, Any
import json
from src.config import (
    WIKIDATA_ENDPOINT,
    WIKIDATA_USER_AGENT,
    DOMAIN,
    RATE_LIMIT_DELAY,
    RATE_LIMIT_BURST_THRESHOLD,
    RATE_LIMIT_BURST_DELAY,
)
from src.wikidata.queries import get_topic_query, get_properties_query, DOMAIN_CONFIGS


def get_topics_from_wikidata(
    domain: str = DOMAIN, limit: int = 20
) -> List[Dict[str, Any]]:
    """Fetch domain-specific topics from Wikidata using SPARQL.

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

    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT, agent=WIKIDATA_USER_AGENT)
    sparql.setReturnFormat(JSON)

    # Get the query for the specified domain
    query = get_topic_query(domain, limit)
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
        logger.debug(
            f"SPARQL Query Result Keys: {next(iter(results['results']['bindings'])).keys() if results['results']['bindings'] else 'No results'}"
        )
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
                # This is the raw topic type value we set in the BIND in our query
                topic_type = result["topicType"]["value"]

            topics[topic_id] = {
                "id": topic_id,
                "title": result["topicLabel"]["value"],
                "wikidata_url": result["topic"]["value"],
                "description": result.get("description", {}).get("value", ""),
                "topic_type": topic_type,
                "properties": {},
            }

    # Get additional properties for each topic
    topic_ids = list(topics.keys())
    redis_client = get_redis_client()

    for i, topic_id in enumerate(tqdm(topic_ids, desc="Fetching topic properties")):
        # Check if we have already fetched properties for this topic
        cache_key = f"wikidata:{domain}:{topic_id}"
        cached_properties = redis_client.hgetall(cache_key)

        if cached_properties:
            # Retrieve properties from cache
            topic = topics[topic_id]

            # Convert cached strings to actual data structures
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
        else:
            # Fetch properties from Wikidata
            success = get_topic_properties(topic_id, topics[topic_id])

            # Cache properties if successful
            if success:
                # Store each property as JSON string
                cache_data = {}
                for key, value in topics[topic_id]["properties"].items():
                    cache_data[key] = json.dumps(value)
                redis_client.hset(cache_key, mapping=cache_data)

            # Rate limiting to respect Wikidata servers
            time.sleep(
                RATE_LIMIT_DELAY
                + (i > 0 and i % RATE_LIMIT_BURST_THRESHOLD == 0)
                * RATE_LIMIT_BURST_DELAY
            )

    return list(topics.values())


# For backward compatibility
def get_programming_topics_from_wikidata(limit: int = 20) -> List[Dict[str, Any]]:
    """Legacy function to maintain backward compatibility."""
    return get_topics_from_wikidata("programming", limit)


def get_topic_properties(topic_id: str, topic: Dict[str, Any]) -> bool:
    """Get detailed properties for a specific topic."""
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT, agent=WIKIDATA_USER_AGENT)
    sparql.setReturnFormat(JSON)

    # Get the properties query
    query = get_properties_query(topic_id)
    sparql.setQuery(query)

    try:
        results = sparql.query().convert()

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

        return True

    except Exception as e:
        logger.error(f"Error fetching properties for {topic_id}: {str(e)}")
        return False
