"""Embedding class for generating vector embeddings."""
import os
from typing import List
from sentence_transformers import SentenceTransformer


class Embedding:
    """Embedding class using BAAI/bge-small-en-v1.5 model."""
    
    # Class-level cache to share model across instances
    _model_cache = {}
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: The name of the sentence-transformer model to use
        """
        self.model_name = model_name
        
        # Use cached model if available
        if model_name in Embedding._model_cache:
            print(f"DEBUG: Using cached embedding model '{model_name}'")
            self.model = Embedding._model_cache[model_name]
        else:
            print(f"DEBUG: Loading embedding model '{model_name}'...")
            self.model = SentenceTransformer(model_name)
            Embedding._model_cache[model_name] = self.model
            print(f"DEBUG: Model loaded and cached")
        
        self.dimension = self.model.get_sentence_embedding_dimension()
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        # BGE models work better with the instruction prefix for documents
        # Use batch encoding for efficiency
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32
        )
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding for a single query text.
        
        Args:
            text: The query text to embed
            
        Returns:
            An embedding vector (as a list of floats)
        """
        # BGE models recommend adding "Represent this sentence for searching relevant passages: " 
        # prefix for queries, but we'll keep it simple for now
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding.tolist()
