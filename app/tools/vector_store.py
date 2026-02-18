from typing import List, Optional
import logging
import os

import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store with OpenAI embeddings.

    Uses OpenAI's text-embedding-3-small model to create embeddings
    and FAISS for efficient similarity search.
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small", dimension: int = 1536) -> None:
        """
        Initialize the FAISS vector store.

        Args:
            embedding_model: OpenAI embedding model to use
            dimension: Embedding dimension (1536 for text-embedding-3-small, 3072 for text-embedding-3-large)
        """
        self.embedding_model = embedding_model
        self.dimension = dimension
        self.client = OpenAI()
        
        # Initialize FAISS index (L2 distance / cosine similarity)
        # Using IndexFlatIP (Inner Product) for cosine similarity after normalization
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Store document texts and metadata
        self._documents: List[str] = []
        self._metadata: List[dict] = []
        
        logger.info("VectorStore: Initialized FAISS index with dimension %d", dimension)

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for a text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            numpy array of embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            # Normalize for cosine similarity
            embedding_array = np.array(embedding, dtype=np.float32)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            return embedding_array
        except Exception as exc:
            logger.error("VectorStore: Failed to get embedding: %s", exc)
            raise

    def add_documents(self, docs: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """
        Add documents to the vector store.

        Args:
            docs: List of document texts to add
            metadatas: Optional list of metadata dicts (one per document)
        """
        if not docs:
            return
        
        logger.info("VectorStore: Adding %d documents to index...", len(docs))
        
        # Generate embeddings for all documents
        embeddings = []
        for doc in docs:
            embedding = self._get_embedding(doc)
            embeddings.append(embedding)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self._documents.extend(docs)
        if metadatas:
            self._metadata.extend(metadatas)
        else:
            self._metadata.extend([{}] * len(docs))
        
        logger.info("VectorStore: Successfully added %d documents. Total documents: %d", 
                   len(docs), len(self._documents))

    def similarity_search(self, query: str, k: int = 3) -> List[str]:
        """
        Search for similar documents using FAISS.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of document texts (most similar first)
        """
        if self.index.ntotal == 0:
            logger.warning("VectorStore: Index is empty, returning empty results")
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        k = min(k, self.index.ntotal)  # Don't request more than available
        distances, indices = self.index.search(query_vector, k)
        
        # Retrieve documents
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self._documents):
                results.append(self._documents[idx])
        
        logger.info("VectorStore: Found %d similar documents for query", len(results))
        return results

    def similarity_search_with_scores(self, query: str, k: int = 3) -> List[tuple[str, float]]:
        """
        Search for similar documents with similarity scores.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of tuples (document_text, similarity_score)
        """
        if self.index.ntotal == 0:
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)
        
        # Retrieve documents with scores
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if 0 <= idx < len(self._documents):
                results.append((self._documents[idx], float(score)))
        
        return results

    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with stats (num_documents, index_size, etc.)
        """
        return {
            "num_documents": len(self._documents),
            "index_size": self.index.ntotal,
            "dimension": self.dimension,
            "embedding_model": self.embedding_model,
        }


