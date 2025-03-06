"""Configuration settings for the learning path application."""

from pathlib import Path

# Domain Configuration
DOMAIN = "programming"  # Can be changed to "mathematics" or other supported domains

# API Configuration
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_USER_AGENT = "LearningPathGenerator/0.1"
WIKIPEDIA_USER_AGENT = (
    "LearningPathGenerator/0.1 (https://github.com/mNandhu/learning_path)"
)

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_CACHE_EXPIRATION = 86400  # 24 hours in seconds

# Mongo Configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "learning_path"
MONGO_COLLECTION = "topics"

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
