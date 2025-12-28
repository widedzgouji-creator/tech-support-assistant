"""RAG (Retrieval-Augmented Generation) system for document ingestion."""
import asyncio
import os
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

from tech_support.embedding import Embedding

# Load environment variables
load_dotenv()


class RAG:
    """RAG system for ingesting and retrieving documentation."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md'}
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize RAG system with ChromaDB connection.
        
        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        self.collection_name = collection_name
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        
        # Initialize embedding model
        self.embedding = Embedding(model_name=self.embedding_model_name)
        
        # ChromaDB client (lazy initialization)
        self._client = None
        self._collection = None
    
    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(
                    anonymized_telemetry=os.getenv("ANONYMIZED_TELEMETRY", "TRUE") == "TRUE"
                )
            )
        return self._client
    
    def _get_collection(self):
        """Get or create ChromaDB collection."""
        if self._collection is None:
            if not self.collection_name:
                raise ValueError("Collection name must be set before accessing collection")
            
            client = self._get_client()
            # Create or get collection
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
            
            start += self.chunk_size - self.chunk_overlap
            
            # Prevent infinite loop
            if start <= 0:
                break
        
        return chunks if chunks else [text]  # Return at least one chunk
    
    def _validate_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate if a file is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type: {file_path.suffix}. Only .txt and .md files are supported."
        
        return True, None
    
    FAKE_MARKDOWN_CONTENT = {
        "getting-started.md": """# Getting Started

Welcome to the documentation! This guide will help you get up and running quickly.

## Installation

```bash
pip install example-package
```

## Quick Start

Here's a simple example to get you started:

```python
from example import Client

client = Client()
result = client.do_something()
print(result)
```

## Next Steps

- Read the [API Reference](api-reference.md)
- Check out the [Configuration Guide](configuration.md)
""",
        "api-reference.md": """# API Reference

Complete API documentation for all available methods and classes.

## Client Class

### `Client(api_key: str, timeout: int = 30)`

Main client for interacting with the service.

**Parameters:**
- `api_key`: Your API authentication key
- `timeout`: Request timeout in seconds (default: 30)

### `Client.do_something(param: str) -> dict`

Performs an operation with the given parameter.

**Returns:** A dictionary with the operation results.

**Example:**
```python
client = Client(api_key="your-key")
result = client.do_something("test")
```
""",
        "configuration.md": """# Configuration Guide

Learn how to configure the application for your needs.

## Configuration File

Create a `config.yaml` file in your project root:

```yaml
api:
  host: localhost
  port: 8080
  timeout: 30

features:
  experimental: false
  debug_mode: false
```

## Environment Variables

You can also use environment variables:

- `API_HOST`: Override the API host
- `API_PORT`: Override the API port
- `DEBUG`: Enable debug mode (true/false)
""",
        "troubleshooting.md": """# Troubleshooting

Common issues and their solutions.

## Connection Timeouts

If you're experiencing connection timeouts:

1. Check your network connection
2. Increase the timeout value in your config
3. Verify the service is running

## Authentication Errors

If you get authentication errors:

1. Verify your API key is correct
2. Check that your key hasn't expired
3. Ensure you're using the correct environment
""",
        "advanced-features.md": """# Advanced Features

Explore advanced capabilities and use cases.

## Custom Plugins

You can extend functionality with custom plugins:

```python
from example import Plugin

class MyPlugin(Plugin):
    def process(self, data):
        # Your custom logic here
        return modified_data
```

## Performance Tuning

Tips for optimizing performance:

- Use connection pooling
- Enable caching
- Adjust batch sizes
""",
        "security.md": """# Security Best Practices

Important security considerations for production deployments.

## API Key Management

- Never commit API keys to version control
- Use environment variables or secret managers
- Rotate keys regularly

## Network Security

- Always use HTTPS in production
- Implement rate limiting
- Use firewall rules to restrict access
""",
    }
    
    async def ingest(self, folder_path: str, progress_callback: Optional[Callable] = None):
        """
        Ingest documents from a folder into ChromaDB.
        
        Args:
            folder_path: Path to the folder containing documents
            progress_callback: Optional callback function for progress updates
                              Signature: callback(current: int, total: int, filename: str, status: str)
        """
        path = Path(folder_path)
        
        if not path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")
        
        # Get collection
        collection = self._get_collection()
        
        # Find all supported files
        all_files = list(path.rglob("*"))
        text_files = []
        rejected_files = []
        
        for file_path in all_files:
            is_valid, error = self._validate_file(file_path)
            if is_valid:
                text_files.append(file_path)
            elif error and file_path.is_file():
                rejected_files.append((file_path, error))
        
        # Report rejected files
        if rejected_files:
            for file_path, error in rejected_files:
                if progress_callback:
                    progress_callback(0, len(text_files), str(file_path.name), f"REJECTED: {error}")
        
        if not text_files:
            raise ValueError(f"No supported files (.txt, .md) found in {folder_path}")
        
        total_files = len(text_files)
        total_chunks = 0
        
        # Process each file
        for i, file_path in enumerate(text_files, 1):
            try:
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, "Reading...")
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, "Chunking...")
                
                # Chunk the text
                chunks = self._chunk_text(content)
                
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, f"Embedding {len(chunks)} chunks...")
                
                # Generate embeddings
                embeddings = self.embedding.embed_documents(chunks)
                
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, f"Saving to ChromaDB...")
                
                # Prepare metadata and IDs
                relative_path = file_path.relative_to(path)
                ids = [f"{relative_path}_{j}" for j in range(len(chunks))]
                metadatas = [
                    {
                        "filename": file_path.name,
                        "filepath": str(relative_path),
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    }
                    for j in range(len(chunks))
                ]
                
                # Add to ChromaDB
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                
                total_chunks += len(chunks)
                
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, f"✓ Done ({len(chunks)} chunks)")
                
                # Small delay to make progress visible
                await asyncio.sleep(0.1)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(i, total_files, file_path.name, f"ERROR: {str(e)}")
        
        if progress_callback:
            progress_callback(total_files, total_files, "", f"Completed! {total_chunks} total chunks ingested.")
    
    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """
        Search for relevant documents using the query.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of dicts with keys: id, document, metadata, distance
        """
        if not self.collection_name:
            print(f"DEBUG RAG: No collection name set")
            return []
        
        try:
            collection = self._get_collection()
            print(f"DEBUG RAG: Collection '{self.collection_name}' has {collection.count()} items")
            
            # Generate query embedding
            query_embedding = self.embedding.embed_query(query)
            print(f"DEBUG RAG: Generated embedding of dimension {len(query_embedding)}")
            
            # Search ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            print(f"DEBUG RAG: ChromaDB returned {len(results['ids'][0]) if results and results['ids'] else 0} results")
            
            # Format results
            formatted_results = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_document_chunk(self, chunk_id: str) -> Optional[str]:
        """
        Retrieve a specific document chunk by ID.
        
        Args:
            chunk_id: The chunk ID to retrieve
            
        Returns:
            The document text or None if not found
        """
        try:
            collection = self._get_collection()
            result = collection.get(ids=[chunk_id], include=["documents", "metadatas"])
            
            if result and result['documents'] and len(result['documents']) > 0:
                return result['documents'][0]
            return None
            
        except Exception as e:
            print(f"Error retrieving chunk: {e}")
            return None
    
    def get_document(self, filename: str) -> str:
        """
        Retrieve markdown content for a document (fallback to fake content).
        
        Args:
            filename: The filename to retrieve
            
        Returns:
            Markdown content as a string
        """
        return self.FAKE_MARKDOWN_CONTENT.get(
            filename,
            f"# Document Not Found\n\nThe document `{filename}` could not be found."
        )
