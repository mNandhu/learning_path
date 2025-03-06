from SPARQLWrapper import SPARQLWrapper, JSON
import time
from tqdm import tqdm
from logger import logger


def get_programming_topics_from_wikidata(limit=20):
    """Fetch programming-related topics from Wikidata using SPARQL."""
    logger.info("Fetching programming topics from Wikidata...")
    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql", agent="LearningPathGenerator/0.1"
    )
    sparql.setReturnFormat(JSON)

    # Query for programming languages, paradigms, concepts, frameworks, and development
    query = """
    SELECT DISTINCT ?topic ?topicLabel ?description ?topicType ?topicTypeLabel
    WHERE {
      {
        # Programming languages
        ?topic wdt:P31/wdt:P279* wd:Q9143.
        BIND("programming_language" AS ?topicType)
      } UNION {
        # Programming paradigms
        ?topic wdt:P31/wdt:P279* wd:Q80286.
        BIND("programming_paradigm" AS ?topicType)
      } UNION {
        # Programming concepts and data structures
        ?topic wdt:P31/wdt:P279* wd:Q1936517.
        BIND("programming_concept" AS ?topicType)
      } UNION {
        # Software frameworks
        ?topic wdt:P31/wdt:P279* wd:Q1130561.
        BIND("software_framework" AS ?topicType)
      } UNION {
        # Software development
        ?topic wdt:P31/wdt:P279* wd:Q3965310.
        BIND("software_development" AS ?topicType)
      }
      
      OPTIONAL { ?topic schema:description ?description FILTER(LANG(?description) = "en"). }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT """ + str(limit)

    sparql.setQuery(query)

    try:
        results = sparql.query().convert()
    except Exception as e:
        logger.error(f"SPARQL query failed: {str(e)}")
        return []

    # Process results into structured format
    topics = {}
    for result in results["results"]["bindings"]:
        topic_id = result["topic"]["value"].split("/")[-1]

        if topic_id not in topics:
            topics[topic_id] = {
                "id": topic_id,
                "title": result["topicLabel"]["value"],
                "wikidata_url": result["topic"]["value"],
                "description": result.get("description", {}).get("value", ""),
                "topic_type": result.get("topicTypeLabel", {}).get("value", ""),
                "properties": {},
            }

    # Get additional properties for each topic
    topic_ids = list(topics.keys())
    for i, topic_id in enumerate(tqdm(topic_ids, desc="Fetching topic properties")):
        get_topic_properties(topic_id, topics[topic_id])

        # Rate limiting to respect Wikidata servers - more consistent approach
        time.sleep(1 + (i > 0 and i % 5 == 0))  # Sleep 1s normally, 2s every 5 requests

    return list(topics.values())


def get_topic_properties(topic_id, topic):
    """Get detailed properties for a specific topic."""
    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql", agent="LearningPathGenerator/0.1"
    )
    sparql.setReturnFormat(JSON)
    # Query for specific properties relevant to programming topics
    query = f"""
    SELECT ?property ?propertyLabel ?value ?valueLabel
    WHERE {{
      wd:{topic_id} ?prop ?value .
      ?property wikibase:directClaim ?prop .
      
      # Filter for specific properties we're interested in
      FILTER(?prop IN (
        wdt:P31,  # instance of
        wdt:P279, # subclass of
        wdt:P361, # part of
        wdt:P366, # has use
        wdt:P527, # has part
        wdt:P737, # influenced by
        wdt:P1535, # used by
        wdt:P144, # based on
        wdt:P1963, # properties for this type
        wdt:P138, # named after
        wdt:P170, # creator
        wdt:P178, # developer
        wdt:P571, # inception/creation date
        wdt:P856, # official website
        wdt:P3966, # programming paradigm
        wdt:P277   # programming language
      ))
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

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
        # Ensure we return a value to indicate failure
        return False
