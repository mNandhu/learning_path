import requests
import wikipedia
from bs4 import BeautifulSoup
import time
import json
import re
from tqdm import tqdm
from logger import logger
from ..database.redis import get_redis_client

# Configure user-agent for all Wikipedia API requests
USER_AGENT = "LearningPathGenerator/0.1 (https://github.com/yourusername/learning_path)"
wikipedia.set_user_agent(USER_AGENT)


def enrich_with_wikipedia(topics):
    """Enrich Wikidata topics with information from Wikipedia."""
    logger.info("Enriching topics with Wikipedia data...")

    for topic in tqdm(topics, desc="Processing Wikipedia data"):
        title = topic["title"]

        try:
            # Try to get the Wikipedia page directly
            redis_client = get_redis_client()
            cache_key = f"wikipedia:{title}"
            cached_data = redis_client.get(cache_key)

            if cached_data:
                page_data = json.loads(cached_data)
                topic.update(page_data)
                logger.debug(f"Retrieved Wikipedia data for '{title}' from cache")
            else:
                page = wikipedia.page(title, auto_suggest=False)
                add_wikipedia_data(topic, page)
                # Cache the Wikipedia data
                page_data = {
                    "url": topic["url"],
                    "summary": topic["summary"],
                    "categories": topic["categories"],
                    "content": topic["content"],
                    "sections": topic["sections"],
                }
                redis_client.set(
                    cache_key, json.dumps(page_data), ex=3600
                )  # Cache for 1 hour
                logger.debug(f"Cached Wikipedia data for '{title}'")

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
                        except Exception as ex:
                            logger.debug(f"Failed with option '{option}': {str(ex)}")
                            continue
                if found:
                    break

            # Fallback to first option if no match found
            if not found and options:
                try:
                    page = wikipedia.page(options[0], auto_suggest=False)
                    add_wikipedia_data(topic, page)
                except Exception as ex:
                    logger.warning(
                        f"Failed with fallback option '{options[0]}': {str(ex)}"
                    )
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
                except Exception as ex:
                    logger.debug(f"Search failed for '{term}': {str(ex)}")
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
    content = re.sub(r"\[\d+]", "", page.content)

    # Get page sections from TOC
    sections = []
    try:
        # Use requests with a user agent header
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(page.url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        soup = BeautifulSoup(response.text, features="html.parser")
        toc = soup.find(id="toc")
        if toc:
            sections = [li.a.text.strip() for li in toc.find_all("li") if li.a]
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch TOC for {page.title}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error parsing TOC for {page.title}: {str(e)}")

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
