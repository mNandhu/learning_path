"""Embedding service for text-to-vector conversion using Ollama."""

import re
import uuid
import time
import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple
from threading import Lock

import ollama
from dotenv import load_dotenv

from src.logger import get_logger
from src.database.chromadb import ChromaDBClient

# Load environment variables
load_dotenv()

# Configure Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Configure chunking
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "500"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "50"))

# Collection creation lock to prevent race conditions
_collection_locks = {}
_global_lock = Lock()

logger = get_logger(__name__)


def get_collection_lock(collection_name: str) -> Lock:
    """Get or create a lock for a specific collection."""
    with _global_lock:
        if collection_name not in _collection_locks:
            _collection_locks[collection_name] = Lock()
        return _collection_locks[collection_name]


async def generate_embedding_async(text: str) -> List[float]:
    """Generate embeddings for text using Ollama API asynchronously.

    Args:
        text: Text to generate embeddings for

    Returns:
        List of floating point numbers representing the embedding vector

    Raises:
        Exception: If embedding generation fails
    """
    try:
        # Use ollama.AsyncClient for async operations
        ollama_client = ollama.AsyncClient(host=OLLAMA_BASE_URL)
        response = await ollama_client.embed(model=OLLAMA_EMBEDDING_MODEL, input=text)
        return response["embedding"]

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise


def generate_embedding(text: str) -> List[float]:
    """Generate embeddings for text using Ollama API synchronously.

    Args:
        text: Text to generate embeddings for

    Returns:
        List of floating point numbers representing the embedding vector
    """
    try:
        # Use ollama.Client for sync operations
        ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        response = ollama_client.embed(model=OLLAMA_EMBEDDING_MODEL, input=text)
        return response["embedding"]

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise


async def generate_embeddings_batch_async(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts in parallel.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embedding vectors
    """
    # For a batch of texts, we'll embed them in parallel using tasks
    tasks = [generate_embedding_async(text) for text in texts]
    return await asyncio.gather(*tasks)


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts in parallel synchronously.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embedding vectors
    """
    try:
        # Use ollama.Client for sync operations with batch input
        ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        embeddings = []

        # Process in batches to avoid overwhelming the server
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            for text in batch_texts:
                response = ollama_client.embed(
                    model=OLLAMA_EMBEDDING_MODEL, text=text
                )
                embeddings.append(response["embedding"])

        return embeddings
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {str(e)}")
        # Check if an event loop is already running
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            logger.warning(
            "An event loop is already running. Falling back to synchronous embedding."
            )
            # If a loop is running, execute tasks synchronously
            embeddings = [generate_embedding(text) for text in texts]
            return embeddings
        else:
            # No loop is running, so we can safely use asyncio.run
            return asyncio.run(generate_embeddings_batch_async(texts))


async def embed_and_store_async(
    chunks: List[str],
    collection_name: str,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> List[str]:
    """Generate embeddings for chunks and store them in ChromaDB asynchronously.

    Args:
        chunks: List of text chunks to embed and store
        collection_name: Name of the ChromaDB collection to store embeddings in
        metadatas: Optional list of metadata dictionaries for each chunk
        ids: Optional list of IDs for the chunks. If not provided, UUIDs will be generated

    Returns:
        List of IDs for the stored chunks
    """
    if not chunks:
        logger.warning("No chunks provided to embed_and_store_async")
        return []

    # Initialize ChromaDB client
    chroma_client = ChromaDBClient()

    # Use collection lock to ensure thread safety
    collection_lock = get_collection_lock(collection_name)

    # Set up the collection first
    with collection_lock:
        try:
            # Create or get the collection with metadata
            metadata = {"created_at": time.time(), "description": "Topic embeddings"}
            collection = chroma_client.get_or_create_collection(
                name=collection_name, metadata=metadata
            )
            logger.debug(f"Using collection: {collection_name}")
        except Exception as e:
            logger.error(
                f"Failed to set up ChromaDB collection '{collection_name}': {str(e)}"
            )
            raise

    # Generate embeddings for all chunks
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    try:
        embeddings = await generate_embeddings_batch_async(chunks)
    except Exception as e:
        logger.error(f"Failed to generate embeddings for chunks: {str(e)}")
        raise

    # Generate IDs if not provided
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in chunks]

    # Store the embeddings
    logger.info(
        f"Storing {len(chunks)} chunks in ChromaDB collection '{collection_name}'"
    )
    try:
        # Add documents directly using the collection reference we already have
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        logger.info(
            f"Successfully stored {len(chunks)} embeddings in collection '{collection_name}'"
        )
    except Exception as e:
        logger.error(
            f"Failed to store embeddings in collection '{collection_name}': {str(e)}"
        )
        raise

    return ids


def embed_and_store(
    chunks: List[str],
    collection_name: str,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> List[str]:
    """Generate embeddings for chunks and store them in ChromaDB.

    Args:
        chunks: List of text chunks to embed and store
        collection_name: Name of the ChromaDB collection to store embeddings in
        metadatas: Optional list of metadata dictionaries for each chunk
        ids: Optional list of IDs for the chunks. If not provided, UUIDs will be generated

    Returns:
        List of IDs for the stored chunks
    """
    # This is only for standalone use, not from an async context
    return asyncio.run(
        embed_and_store_async(
            chunks=chunks, collection_name=collection_name, metadatas=metadatas, ids=ids
        )
    )


async def query_by_text_async(
    query_text: str,
    collection_name: str,
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, List]:
    """Query ChromaDB collection using text asynchronously.

    Args:
        query_text: Text to query with
        collection_name: Name of the collection to query
        n_results: Number of results to return
        where: Optional filter criteria

    Returns:
        Dictionary containing query results
    """
    # Generate embedding for query text
    query_embedding = await generate_embedding_async(query_text)

    # Query ChromaDB
    chroma_client = ChromaDBClient()
    return chroma_client.query_collection(
        collection_name=collection_name,
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
    )


def query_by_text(
    query_text: str,
    collection_name: str,
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, List]:
    """Query ChromaDB collection using text.

    Args:
        query_text: Text to query with
        collection_name: Name of the collection to query
        n_results: Number of results to return
        where: Optional filter criteria

    Returns:
        Dictionary containing query results
    """
    return asyncio.run(
        query_by_text_async(
            query_text=query_text,
            collection_name=collection_name,
            n_results=n_results,
            where=where,
        )
    )


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split text into chunks of specified size with overlap.

    Args:
        text: Text to split into chunks
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    # Split text into sentences to avoid breaking in the middle of a sentence
    # This is a simple sentence splitting, could be improved
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            # Save the current chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Start a new chunk
            if len(sentence) > chunk_size:
                # If sentence is longer than chunk_size, we need to break it
                remaining = sentence
                while len(remaining) > chunk_size:
                    chunks.append(remaining[:chunk_size])
                    remaining = remaining[chunk_size - chunk_overlap :]
                current_chunk = remaining + " "
            else:
                current_chunk = sentence + " "

    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


async def process_topic_content_async(
    topic: Dict[str, Any],
    collection_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> Tuple[Dict[str, Any], List[str]]:
    """Process a topic's content, chunk it, and store embeddings in ChromaDB asynchronously.

    Args:
        topic: The topic dictionary containing content
        collection_name: Name of the collection to store embeddings
        chunk_size: Size of each content chunk
        chunk_overlap: Overlap between chunks

    Returns:
        Tuple of (updated topic with reference IDs, list of chunk IDs)
    """
    topic_id = topic.get("id", "unknown")
    content = topic.get("content", "")
    summary = topic.get("summary", "")

    # Skip if no content
    if not content and not summary:
        logger.warning(f"Topic {topic_id} has no content or summary to embed")
        return topic, []

    # Create a combined text for embedding (or separate if preferred)
    if content:
        chunks = chunk_text(content, chunk_size, chunk_overlap)
    else:
        chunks = [summary]  # Use summary if content is not available

    # Skip if we couldn't create chunks
    if not chunks:
        logger.warning(f"Topic {topic_id} yielded no chunks to embed")
        return topic, []

    # Generate metadata for each chunk
    topic_label = topic.get("title", topic.get("label", ""))  # Try both title and label
    metadatas = [
        {
            "topic_id": topic_id,
            "topic_label": topic_label,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "source": "wikidata_wikipedia",
        }
        for i in range(len(chunks))
    ]

    # Generate unique IDs for chunks - ensure they're unique across multiple runs
    chunk_ids = [f"{topic_id}_{i}_{int(time.time())}" for i in range(len(chunks))]

    # Store chunks in ChromaDB
    try:
        # Use a single call to embed_and_store_async with better error handling
        chunk_ids = await embed_and_store_async(
            chunks=chunks,
            collection_name=collection_name,
            metadatas=metadatas,
            ids=chunk_ids,
        )

        # Update topic with reference to ChromaDB
        topic["embedding_refs"] = {
            "collection": collection_name,
            "chunk_ids": chunk_ids,
            "timestamp": time.time(),
        }

        logger.info(f"Successfully embedded topic {topic_id} into {len(chunks)} chunks")

    except Exception as e:
        # More specific error handling with detailed message
        logger.error(f"Failed to embed topic {topic_id}: {str(e)}")
        # Don't propagate the exception - just continue with the next topic
        # Set an error flag in the topic so we know it failed
        topic["embedding_error"] = str(e)

    return topic, chunk_ids


def process_topic_content(
    topic: Dict[str, Any],
    collection_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> Tuple[Dict[str, Any], List[str]]:
    """Process a topic's content, chunk it, and store embeddings in ChromaDB.

    Args:
        topic: The topic dictionary containing content
        collection_name: Name of the collection to store embeddings
        chunk_size: Size of each content chunk
        chunk_overlap: Overlap between chunks

    Returns:
        Tuple of (updated topic with reference IDs, list of chunk IDs)
    """
    # This is only for standalone use, not from an async context
    return asyncio.run(
        process_topic_content_async(
            topic=topic,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    )


async def process_topics_batch_async(
    topics: List[Dict[str, Any]],
    collection_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Process a batch of topics asynchronously, chunking their content and storing embeddings.

    Args:
        topics: List of topic dictionaries
        collection_name: Name of the collection to store embeddings
        chunk_size: Size of each content chunk
        chunk_overlap: Overlap between chunks

    Returns:
        Updated topics with reference IDs to ChromaDB
    """
    updated_topics = []
    total_chunks = 0

    for topic in topics:
        updated_topic, chunk_ids = await process_topic_content_async(
            topic=topic,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        updated_topics.append(updated_topic)
        total_chunks += len(chunk_ids)

    logger.info(
        f"Processed {len(topics)} topics into {total_chunks} chunks in ChromaDB"
    )
    return updated_topics


def process_topics_batch(
    topics: List[Dict[str, Any]],
    collection_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Process a batch of topics, chunking their content and storing embeddings.

    Args:
        topics: List of topic dictionaries
        collection_name: Name of the collection to store embeddings
        chunk_size: Size of each content chunk
        chunk_overlap: Overlap between chunks

    Returns:
        Updated topics with reference IDs to ChromaDB
    """
    # This is only for standalone use, not from an async context
    return asyncio.run(
        process_topics_batch_async(
            topics=topics,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    )
