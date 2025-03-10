# Changelog

## [Release 0.1.1]

- Initial entry for the changelog.
- Added a new instruction in custom instructions.
- Added vector embedding capabilities using Ollama and ChromaDB:
  - Created ChromaDB integration in `src/database/chromadb.py`
  - Implemented embedding generation in `src/embeddings/service.py`
  - Added text chunking functionality for better embedding quality
  - Enhanced MongoDB integration with embedding references
  - Added command-line options to generate embeddings for topics
- Fixed logger implementation:
  - Standardized using `get_logger(__name__)` across all modules
  - Removed root logger for backward compatibility
  - Enhanced logging format for Windows and redirected output
- Fixed ChromaDB collection handling:
  - Added proactive collection creation before embeddings are generated
  - Improved error handling for collection operations
  - Fixed "collection does not exist" errors during embedding process
