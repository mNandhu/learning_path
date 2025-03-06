from sparql import get_programming_topics_from_wikidata
from wikipedia import enrich_with_wikipedia
from knowledge_graph import create_knowledge_graph_data
import json
from logger import logger


def main():
    try:
        # Get topics from Wikidata
        topics = get_programming_topics_from_wikidata(limit=20)

        if not topics:
            logger.error("Failed to retrieve topics from Wikidata")
            return

        # Enrich with Wikipedia data
        enriched_topics = enrich_with_wikipedia(topics)

        # Create knowledge graph data
        knowledge_graph_data = create_knowledge_graph_data(enriched_topics)

        # Save to JSON file
        output_file = "programming_knowledge_graph.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_graph_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Successfully saved data for {len(topics)} programming topics to {output_file}"
        )

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
