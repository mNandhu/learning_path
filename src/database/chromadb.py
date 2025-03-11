"""ChromaDB integration for vector database storage and retrieval."""

import chromadb
import logging
from typing import Dict, List, Optional, Any
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from src.logger import get_logger

# Initialize logger with module name
logger = get_logger(__name__)

# Reduce excessive logging from chromadb's own logger
chromadb_logger = logging.getLogger("chromadb")
chromadb_logger.setLevel(logging.WARNING)


class ChromaDBClient:
    """ChromaDB client wrapper for vector database operations."""

    _instance = None
    _client: Optional[ClientAPI] = None

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for ChromaDB client."""
        if cls._instance is None:
            cls._instance = super(ChromaDBClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_directory: str = "./chroma"):
        """Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        if self._initialized:
            return

        self.persist_directory = persist_directory

        # Initialize client
        try:
            self._client = chromadb.Client(
                Settings(
                    persist_directory=self.persist_directory,
                    is_persistent=True,
                    anonymized_telemetry=False,
                )
            )
            logger.info(
                f"ChromaDB client initialized with persistence at {self.persist_directory}"
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise

    @property
    def client(self) -> ClientAPI:
        """Get the ChromaDB client instance.

        Returns:
            The ChromaDB client
        """
        if self._client is None:
            raise RuntimeError("ChromaDB client not initialized")
        return self._client

    def list_collections(self) -> List[str]:
        """List all collection names in ChromaDB.

        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [collection.name for collection in collections]

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Name of the collection

        Returns:
            True if the collection exists, False otherwise
        """
        try:
            self.client.get_collection(name=name)
            return True
        except (ValueError, InvalidCollectionException):
            return False

    def get_or_create_collection(
        self, name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Collection:
        """Get or create a collection.

        Args:
            name: Name of the collection
            metadata: Optional metadata for the collection

        Returns:
            The collection instance
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.debug(f"Retrieved existing collection: {name}")
            return collection
        except (ValueError, InvalidCollectionException):
            # If the collection doesn't exist, create it
            logger.info(f"Creating new collection: {name}")
            return self.client.create_collection(name=name, metadata=metadata)

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents with embeddings to a collection.

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            ids: List of document IDs
            metadatas: Optional list of metadata dictionaries
        """
        collection = self.get_or_create_collection(collection_name)

        collection.add(
            documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas
        )

        logger.info(
            f"Added {len(documents)} documents to collection '{collection_name}'"
        )

    def query_collection(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List]:
        """Query a collection using embeddings.

        Args:
            collection_name: Name of the collection
            query_embeddings: List of embedding vectors to query with
            n_results: Number of results to return
            where: Optional filter criteria

        Returns:
            Dictionary containing query results
        """
        # Check if collection exists first
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")

        # Get the collection
        collection = self.client.get_collection(name=collection_name)

        results = collection.query(
            query_embeddings=query_embeddings, n_results=n_results, where=where
        )

        logger.info(
            f"Queried collection '{collection_name}' with {len(query_embeddings)} embeddings"
        )
        return results

    def query_by_ids(
        self,
        collection_name: str,
        ids: List[str],
        limit: int = 5,
    ) -> Dict[str, List]:
        """Query a collection using document IDs.

        Args:
            collection_name: Name of the collection
            ids: List of document IDs to query
            limit: Number of results to return

        Returns:
            Dictionary containing query results
        """
        # Check if collection exists first
        if not self.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")

        # Get the collection
        collection = self.client.get_collection(name=collection_name)

        results = collection.get(ids=ids, limit=limit)

        logger.info(
            f"Queried collection '{collection_name}' with {len(ids)} document IDs"
        )
        return results
