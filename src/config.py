"""Configuration settings for the learning path application."""

from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# Domain Configuration
DOMAIN = "programming"  # Can be changed to "mathematics" or other supported domains

# API Configuration
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_USER_AGENT = "LearningPathGenerator/0.1"
WIKIPEDIA_USER_AGENT = (
    "LearningPathGenerator/0.1 (https://github.com/mNandhu/learning_path)"
)

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)
REDIS_CACHE_EXPIRATION = 86400  # 24 hours in seconds

# Mongo Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "learning_path")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "topics")

# File Paths
OUTPUT_DIR = Path("output")
LOG_DIR = Path("logs")

# Knowledge Graph Settings
DEFAULT_GRAPH_LIMIT = 100

# Domain-specific color themes
DOMAIN_COLORS = {
    "programming": {
        "programming_language": "#66c2a5",
        "programming_paradigm": "#fc8d62",
        "programming_concept": "#8da0cb",
        "software_framework": "#e78ac3",
        "software_development": "#a6d854",
        "unknown": "#cccccc",
    },
    "mathematics": {
        "mathematical_concept": "#4e79a7",
        "mathematical_theorem": "#f28e2b",
        "mathematical_field": "#e15759",
        "mathematician": "#76b7b2",
        "mathematical_object": "#59a14f",
        "unknown": "#cccccc",
    },
}

# Current topic type colors based on selected domain
TOPIC_TYPE_COLORS = DOMAIN_COLORS.get(DOMAIN, DOMAIN_COLORS["programming"])

# Rate Limiting
RATE_LIMIT_DELAY = 0.5
RATE_LIMIT_BURST_THRESHOLD = 5
RATE_LIMIT_BURST_DELAY = 0.5
BATCH_SIZE = 50

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
