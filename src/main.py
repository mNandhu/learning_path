from src.wikidata.sparql import get_programming_topics_from_wikidata
from src.wikipedia_.api import enrich_with_wikipedia
from knowledge_graph.knowledge_graph import create_knowledge_graph_data
import json
from logger import logger
from pathlib import Path
import time
from src.knowledge_graph.visualize_graph import generate_graphml_and_save_as_html


def main():
    try:
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Add timestamp to output filename for versioning
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"programming_knowledge_graph_{timestamp}.json"
        enriched_output_file = (
            output_dir / f"enriched_programming_topics_{timestamp}.json"
        )

        # Get topics from Wikidata
        topics = get_programming_topics_from_wikidata(limit=50)

        if not topics:
            logger.error("Failed to retrieve topics from Wikidata")
            return

        logger.info(f"Successfully retrieved {len(topics)} topics from Wikidata")

        # Enrich with Wikipedia data
        enriched_topics = enrich_with_wikipedia(topics)

        # Save enriched topics to JSON file
        with open(enriched_output_file, "w", encoding="utf-8") as f:
            json.dump(enriched_topics, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully saved enriched topics to {enriched_output_file}")
        logger.info(f"Successfully enriched {len(topics)} topics with Wikipedia data")

        # Create knowledge graph data
        knowledge_graph_data = create_knowledge_graph_data(enriched_topics)

        # Add metadata to the output
        knowledge_graph_data["metadata"] = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "topic_count": len(topics),
            "edge_count": len(knowledge_graph_data["edges"]),
            "filename": output_file.name,
        }

        # Save to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_graph_data, f, ensure_ascii=False, indent=2)

        # Generate and save knowledge graph visualization
        generate_graphml_and_save_as_html(knowledge_graph_data)

        logger.info(
            f"Successfully saved knowledge graph with {len(topics)} topics and "
            f"{len(knowledge_graph_data['edges'])} edges to {output_file}"
        )

    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
