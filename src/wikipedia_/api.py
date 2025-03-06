import requests
import wikipedia
from bs4 import BeautifulSoup
import time
import json
import re
from tqdm import tqdm
from src.logger import logger
from typing import List, Dict, Any
from ..database.redis import get_redis_client
from src.config import WIKIPEDIA_USER_AGENT, REDIS_CACHE_EXPIRATION

# Configure user-agent for all Wikipedia API requests
wikipedia.set_user_agent(WIKIPEDIA_USER_AGENT)


def enrich_with_wikipedia(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich Wikidata topics with information from Wikipedia.

    Args:
        topics: List of topic dictionaries from Wikidata

    Returns:
        The same list of topics with added Wikipedia information
    """
    logger.info("Enriching topics with Wikipedia data...")

    redis_client = get_redis_client()

    for topic in tqdm(topics, desc="Processing Wikipedia data"):
        title = topic["title"]

        try:
            # Try to get the Wikipedia page from cache first
            cache_key = f"wikipedia:{title}"
            cached_data = redis_client.get(cache_key)

            if cached_data:
                try:
                    page_data = json.loads(cached_data)
                    topic.update(page_data)
                    logger.debug(f"Retrieved Wikipedia data for '{title}' from cache")
                    continue
                except json.JSONDecodeError:
                    logger.warning(
                        f"Invalid cache data for '{title}', fetching fresh data"
                    )
                    # Continue to fetch fresh data

            # No valid cache, fetch from Wikipedia API
            try:
                page = wikipedia.page(title, auto_suggest=False)
                add_wikipedia_data(topic, page)

                # Cache the Wikipedia data
                page_data = {
                    "url": topic.get("url", ""),
                    "summary": topic.get("summary", ""),
                    "categories": topic.get("categories", []),
                    "content": topic.get("content", ""),
                    "sections": topic.get("sections", []),
                }

                try:
                    redis_client.set(
                        cache_key, json.dumps(page_data), ex=REDIS_CACHE_EXPIRATION
                    )
                    logger.debug(f"Cached Wikipedia data for '{title}'")
                except Exception as cache_error:
                    logger.warning(
                        f"Failed to cache data for '{title}': {str(cache_error)}"
                    )

                # Rate limiting for Wikipedia - only if not using cache
                time.sleep(0.5)

            except wikipedia.exceptions.DisambiguationError as e:
                handle_disambiguation(topic, title, e.options)
            except wikipedia.exceptions.PageError:
                handle_page_not_found(topic, title)
            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error while fetching '{title}': {str(e)}")
                set_empty_wikipedia_data(topic, f"Network error: {str(e)}")
            except Exception as e:
                logger.warning(f"Error processing '{title}': {str(e)}")
                set_empty_wikipedia_data(topic, f"Error: {str(e)}")

        except Exception as e:
            logger.error(
                f"Unexpected error for topic '{title}': {str(e)}", exc_info=True
            )
            set_empty_wikipedia_data(topic, "Internal processing error")

    return topics


def handle_disambiguation(
    topic: Dict[str, Any], title: str, options: List[str]
) -> None:
    """Handle disambiguation pages by trying programming-related options.

    Args:
        topic: The topic dictionary to update
        title: The original topic title
        options: List of disambiguation options from Wikipedia
    """
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
            logger.warning(f"Failed with fallback option '{options[0]}': {str(ex)}")
            set_empty_wikipedia_data(
                topic, f"Could not resolve disambiguation for {title}"
            )
    else:
        set_empty_wikipedia_data(topic, f"No suitable Wikipedia page found for {title}")


def handle_page_not_found(topic: Dict[str, Any], title: str) -> None:
    """Handle page not found errors by trying searches with additional terms.

    Args:
        topic: The topic dictionary to update
        title: The original topic title
    """
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


def add_wikipedia_data(topic: Dict[str, Any], page: wikipedia.WikipediaPage) -> None:
    """Add Wikipedia data to a topic.

    Args:
        topic: The topic dictionary to update
        page: The Wikipedia page object
    """
    # Extract clean content without citation markers
    content = re.sub(r"\[\d+]", "", page.content)

    # Get page sections from TOC
    sections = []
    try:
        # Use requests with a user agent header
        headers = {"User-Agent": WIKIPEDIA_USER_AGENT}
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


def set_empty_wikipedia_data(topic: Dict[str, Any], message: str) -> None:
    """Set empty Wikipedia data with an error message.

    Args:
        topic: The topic dictionary to update
        message: Error message to include in the summary
    """
    topic.update(
        {"url": "", "summary": message, "categories": [], "content": "", "sections": []}
    )
