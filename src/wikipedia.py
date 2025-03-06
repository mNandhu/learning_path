import requests
import wikipedia
from bs4 import BeautifulSoup
import time
import re
from tqdm import tqdm
from logger import logger


def enrich_with_wikipedia(topics):
    """Enrich Wikidata topics with information from Wikipedia."""
    logger.info("Enriching topics with Wikipedia data...")

    for topic in tqdm(topics, desc="Processing Wikipedia data"):
        title = topic["title"]

        try:
            # Try to get the Wikipedia page directly
            page = wikipedia.page(title, auto_suggest=False)
            add_wikipedia_data(topic, page)

        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages
            options = e.options
            found = False

            # Try with programming-related suffixes
            for suffix in [
                "programming",
                "programming language",
                "computer science",
                "software",
            ]:
                for option in options:
                    if suffix.lower() in option.lower():
                        try:
                            page = wikipedia.page(option, auto_suggest=False)
                            add_wikipedia_data(topic, page)
                            found = True
                            break
                        except Exception:
                            continue
                if found:
                    break

            # Fallback to first option if no match found
            if not found and options:
                try:
                    page = wikipedia.page(options[0], auto_suggest=False)
                    add_wikipedia_data(topic, page)
                except Exception:
                    set_empty_wikipedia_data(
                        topic, f"Could not resolve disambiguation for {title}"
                    )
            else:
                set_empty_wikipedia_data(
                    topic, f"No suitable Wikipedia page found for {title}"
                )

        except wikipedia.exceptions.PageError:
            # Try search with additional terms if direct page lookup fails
            search_terms = [
                f"{title} programming",
                f"{title} computing",
                f"{title} computer science",
                f"{title} software",
            ]

            found = False
            for term in search_terms:
                try:
                    results = wikipedia.search(term)
                    if results:
                        page = wikipedia.page(results[0], auto_suggest=False)
                        add_wikipedia_data(topic, page)
                        found = True
                        break
                except Exception:
                    continue

            if not found:
                set_empty_wikipedia_data(topic, f"No Wikipedia page found for {title}")

        except Exception as e:
            logger.warning(f"Error processing {title}: {str(e)}")
            set_empty_wikipedia_data(topic, f"Error: {str(e)}")

        # Rate limiting for Wikipedia
        time.sleep(1)

    return topics


def add_wikipedia_data(topic, page):
    """Add Wikipedia data to a topic."""
    # Extract clean content without citation markers
    content = re.sub(r"\[\d+\]", "", page.content)

    # Get page sections from TOC
    sections = []
    try:
        soup = BeautifulSoup(requests.get(page.url).text, "html.parser")
        toc = soup.find(id="toc")
        if toc:
            sections = [li.a.text.strip() for li in toc.find_all("li") if li.a]
    except Exception:
        pass

    topic.update(
        {
            "url": page.url,
            "summary": page.summary,
            "categories": page.categories,
            "content": content,
            "sections": sections,
        }
    )


def set_empty_wikipedia_data(topic, message):
    """Set empty Wikipedia data with an error message."""
    topic.update(
        {"url": "", "summary": message, "categories": [], "content": "", "sections": []}
    )
