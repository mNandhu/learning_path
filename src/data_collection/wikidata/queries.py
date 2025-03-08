"""SPARQL query templates for different domain knowledge graphs."""

# Domain configurations with their respective topic types and Wikidata entity IDs
DOMAIN_CONFIGS = {
    "programming": {
        "name": "Programming",
        "topics": [
            {
                "type": "object_oriented_programming",
                "entity_id": "Q79872",
                "description": "programming paradigm based on the concept of objects",
            },
            {
                "type": "programming_language",
                "entity_id": "Q9143",
                "description": "Programming languages",
            },
            {
                "type": "programming_paradigm",
                "entity_id": "Q188267",
                "description": "Programming paradigms",
            },
            {
                "type": "software_framework",
                "entity_id": "Q271680",
                "description": "Software frameworks",
            },
            {
                "type": "software_development",
                "entity_id": "Q638608",
                "description": "Software development",
            },
            {
                "type": "computer_programming",
                "entity_id": "Q80006",
                "description": "the process of designing and building an executable computer program to accomplish a specific computing result or to perform a specific task",
            },
        ],
    },
    "mathematics": {
        "name": "Mathematics",
        "topics": [
            {
                "type": "mathematical_concept",
                "entity_id": "Q2754677",
                "description": "Mathematical concepts",
            },
            {
                "type": "mathematical_theorem",
                "entity_id": "Q47317",
                "description": "Mathematical theorems",
            },
            {
                "type": "mathematical_field",
                "entity_id": "Q12482",
                "description": "Fields of mathematics",
            },
            {
                "type": "mathematician",
                "entity_id": "Q170790",
                "description": "Mathematicians",
            },
            {
                "type": "mathematical_object",
                "entity_id": "Q246672",
                "description": "Mathematical objects",
            },
        ],
    },
}

# Properties we're interested in for all domains
TOPIC_PROPERTIES = [
    {"id": "P31", "description": "instance of"},
    {"id": "P279", "description": "subclass of"},
    {"id": "P361", "description": "part of"},
    {"id": "P366", "description": "has use"},
    {"id": "P527", "description": "has part"},
    {"id": "P737", "description": "influenced by"},
    {"id": "P1535", "description": "used by"},
    {"id": "P144", "description": "based on"},
    {"id": "P1963", "description": "properties for this type"},
    {"id": "P138", "description": "named after"},
    {"id": "P170", "description": "creator"},
    {"id": "P178", "description": "developer"},
    {"id": "P571", "description": "inception/creation date"},
    {"id": "P856", "description": "official website"},
]


def get_topic_query(domain: str, limit: int) -> str:
    """Generate a SPARQL query for a specific domain's topics.

    Args:
        domain: The domain to query (e.g., "programming" or "mathematics")
        limit: Maximum number of results to return

    Returns:
        SPARQL query string for the requested domain
    """
    if domain not in DOMAIN_CONFIGS:
        raise ValueError(
            f"Unknown domain: {domain}. Available domains: {list(DOMAIN_CONFIGS.keys())}"
        )

    # Start building the query
    query = """
    SELECT DISTINCT ?topic ?topicLabel ?description ?topicType ?topicTypeLabel
    WHERE {
    """

    # Add UNION blocks for each topic type in the domain
    topic_blocks = []
    for topic_config in DOMAIN_CONFIGS[domain]["topics"]:
        topic_block = f"""
      {{
        # {topic_config["description"]}
        ?topic wdt:P31/wdt:P279* wd:{topic_config["entity_id"]}.
        BIND("{topic_config["type"]}" AS ?topicType)
      }}"""
        topic_blocks.append(topic_block)

    query += " UNION ".join(topic_blocks)

    # Add the rest of the query
    query += """
      
      OPTIONAL { ?topic schema:description ?description FILTER(LANG(?description) = "en"). }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    LIMIT """ + str(limit)

    return query


def get_properties_query(topic_id: str) -> str:
    """Generate a SPARQL query for properties of a specific topic.

    Args:
        topic_id: The Wikidata entity ID (e.g., Q123)

    Returns:
        SPARQL query string for the topic's properties
    """
    # Build a list of property IDs for the FILTER clause
    property_ids = [f"wdt:{prop['id']}" for prop in TOPIC_PROPERTIES]
    filter_clause = ", ".join(property_ids)

    return f"""
    SELECT ?property ?propertyLabel ?value ?valueLabel
    WHERE {{
      wd:{topic_id} ?prop ?value .
      ?property wikibase:directClaim ?prop .
      
      # Filter for specific properties we're interested in
      FILTER(?prop IN (
        {filter_clause}
      ))
      
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
