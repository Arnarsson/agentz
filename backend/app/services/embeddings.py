"""Embeddings service for generating and managing vector embeddings."""
from typing import List, Dict, Any, Optional, Union
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from app.core.config import settings
from app.core.errors import EmbeddingError
import os

class EmbeddingsService:
    """Service for managing embeddings and vector similarity search."""

    def __init__(self):
        """Initialize the embeddings service."""
        try:
            # Ensure data directory exists
            os.makedirs("data/chromadb", exist_ok=True)

            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path="data/chromadb",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Initialize OpenAI embedding function
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-ada-002"
            )

            # Create or get collections with proper metadata and settings
            self.memories_collection = self.client.get_or_create_collection(
                name="agent_memories",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Agent memory embeddings",
                    "hnsw:space": "cosine"  # Use cosine similarity for memory matching
                }
            )

            self.knowledge_collection = self.client.get_or_create_collection(
                name="knowledge_base",
                embedding_function=self.embedding_function,
                metadata={
                    "description": "Knowledge base embeddings",
                    "hnsw:space": "cosine"  # Use cosine similarity for knowledge matching
                }
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize ChromaDB: {str(e)}")

    async def generate_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text using OpenAI's API."""
        try:
            if isinstance(text, str):
                text = [text]
            
            # Generate embeddings
            embeddings = self.embedding_function(text)
            
            return embeddings[0] if len(embeddings) == 1 else embeddings
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}")

    async def add_memory_embedding(
        self,
        memory_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add a memory embedding to ChromaDB."""
        try:
            # Use upsert instead of add to handle potential duplicates
            self.memories_collection.upsert(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to add memory embedding: {str(e)}")

    async def add_knowledge_embedding(
        self,
        entry_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Add a knowledge base entry embedding to ChromaDB."""
        try:
            # Use upsert instead of add to handle potential duplicates
            self.knowledge_collection.upsert(
                ids=[entry_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to add knowledge embedding: {str(e)}")

    async def query_similar_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Query for similar memories using vector similarity."""
        try:
            # Prepare where clause for filtering
            where = {}
            if agent_id:
                where["agent_id"] = agent_id
            if memory_type:
                where["type"] = memory_type
            if min_importance > 0:
                where["importance"] = {"$gte": min_importance}

            # Query ChromaDB with include parameter for complete results
            results = self.memories_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where if where else None,
                include=["metadatas", "documents", "distances"]
            )

            # Format results
            return [
                {
                    "id": id_,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for id_, doc, meta, dist in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
        except Exception as e:
            raise EmbeddingError(f"Failed to query similar memories: {str(e)}")

    async def query_knowledge_base(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query knowledge base using vector similarity."""
        try:
            # Query ChromaDB with include parameter for complete results
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=limit,
                where=filters,
                include=["metadatas", "documents", "distances"]
            )

            # Format results
            return [
                {
                    "id": id_,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for id_, doc, meta, dist in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
        except Exception as e:
            raise EmbeddingError(f"Failed to query knowledge base: {str(e)}")

    async def update_memory_embedding(
        self,
        memory_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update a memory's embedding in ChromaDB."""
        try:
            # Use upsert for idempotent updates
            self.memories_collection.upsert(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to update memory embedding: {str(e)}")

    async def update_knowledge_embedding(
        self,
        entry_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update a knowledge base entry's embedding in ChromaDB."""
        try:
            # Use upsert for idempotent updates
            self.knowledge_collection.upsert(
                ids=[entry_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to update knowledge embedding: {str(e)}")

    async def delete_memory_embedding(self, memory_id: str) -> None:
        """Delete a memory's embedding from ChromaDB."""
        try:
            self.memories_collection.delete(ids=[memory_id])
        except Exception as e:
            raise EmbeddingError(f"Failed to delete memory embedding: {str(e)}")

    async def delete_knowledge_embedding(self, entry_id: str) -> None:
        """Delete a knowledge base entry's embedding from ChromaDB."""
        try:
            self.knowledge_collection.delete(ids=[entry_id])
        except Exception as e:
            raise EmbeddingError(f"Failed to delete knowledge embedding: {str(e)}")

    async def get_nearest_neighbors(
        self,
        embedding: List[float],
        collection_name: str = "agent_memories",
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get nearest neighbors for a given embedding."""
        try:
            collection = (
                self.memories_collection
                if collection_name == "agent_memories"
                else self.knowledge_collection
            )

            # Query with include parameter for complete results
            results = collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                where=filters,
                include=["metadatas", "documents", "distances"]
            )

            return [
                {
                    "id": id_,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist
                }
                for id_, doc, meta, dist in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
        except Exception as e:
            raise EmbeddingError(f"Failed to get nearest neighbors: {str(e)}")

embeddings_service = EmbeddingsService() 