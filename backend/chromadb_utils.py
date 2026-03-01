"""
chromadb_utils.py — ChromaDB vector database query functions.
Manages the local 'destinations' collection and similarity search.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import chromadb
import numpy as np

logger = logging.getLogger(__name__)

COLLECTION_NAME = "destinations"
CHROMA_STORE_PATH = str(Path(__file__).parent / "chroma_store")

_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def get_client() -> chromadb.PersistentClient:
    """Return or create the persistent ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_STORE_PATH)
        logger.info(f"ChromaDB client initialised at: {CHROMA_STORE_PATH}")
    return _client


def get_collection() -> chromadb.Collection:
    """Return or create the destinations collection."""
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready with {_collection.count()} documents")
    return _collection


def add_destination(
    destination_name: str,
    embedding: list[float],
    tbo_id: str,
    budget_tier: str,
    photo_path: str,
    price_per_person: int,
) -> None:
    """
    Insert a destination into the ChromaDB collection.

    Args:
        destination_name: Human-readable destination name
        embedding: CLIP embedding vector (512 floats)
        tbo_id: TBO identifier string
        budget_tier: 'budget', 'mid-range', or 'premium'
        photo_path: Relative path to the destination's representative photo
        price_per_person: Approximate cost in INR
    """
    collection = get_collection()
    collection.upsert(
        ids=[tbo_id],
        embeddings=[embedding],
        metadatas=[
            {
                "destination": destination_name,
                "tbo_id": tbo_id,
                "budget_tier": budget_tier,
                "photo": photo_path,
                "price_per_person": price_per_person,
            }
        ],
        documents=[destination_name],
    )


def query_similar_destinations(
    query_embedding: np.ndarray,
    budget_tier: str,
    n_results: int = 5,
    exclude_tbo_ids: Optional[list[str]] = None,
) -> list[dict]:
    """
    Find the n most visually similar destinations within budget tier.

    Args:
        query_embedding: CLIP embedding of the user's uploaded photo
        budget_tier: Maximum budget tier ('budget', 'mid-range', 'premium')
        n_results: How many results to return
        exclude_tbo_ids: List of TBO IDs to exclude (already rejected)

    Returns:
        List of dicts with keys: destination, tbo_id, budget_tier, photo,
        price_per_person, similarity_score
    """
    collection = get_collection()

    # Determine which budget tiers are within range
    tier_order = ["budget", "mid-range", "premium"]
    max_tier_index = tier_order.index(budget_tier)
    allowed_tiers = tier_order[: max_tier_index + 1]

    # Build ChromaDB where filter
    if len(allowed_tiers) == 1:
        where_clause = {"budget_tier": {"$eq": allowed_tiers[0]}}
    else:
        where_clause = {"budget_tier": {"$in": allowed_tiers}}

    # Request more results than needed to allow filtering excluded IDs
    fetch_n = n_results + (len(exclude_tbo_ids) if exclude_tbo_ids else 0) + 3

    query_vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding

    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(fetch_n, collection.count()),
            where=where_clause,
            include=["metadatas", "distances", "documents"],
        )
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        # Fallback: query without budget filter
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=min(n_results + 3, collection.count()),
            include=["metadatas", "distances", "documents"],
        )

    if not results["ids"] or not results["ids"][0]:
        return []

    destinations = []
    for i, (metadata, distance) in enumerate(
        zip(results["metadatas"][0], results["distances"][0])
    ):
        tbo_id = metadata.get("tbo_id", "")

        # Skip excluded destinations
        if exclude_tbo_ids and tbo_id in exclude_tbo_ids:
            continue

        # ChromaDB cosine distance = 1 - similarity
        similarity_score = 1.0 - distance

        destinations.append(
            {
                "destination": metadata.get("destination", ""),
                "tbo_id": tbo_id,
                "budget_tier": metadata.get("budget_tier", ""),
                "photo": metadata.get("photo", ""),
                "price_per_person": metadata.get("price_per_person", 0),
                "similarity_score": similarity_score,
            }
        )

        if len(destinations) >= n_results:
            break

    return destinations


def get_collection_count() -> int:
    """Return the number of destinations in the collection."""
    return get_collection().count()


def get_destination_by_id(tbo_id: str) -> Optional[dict]:
    """Fetch a destination's metadata from ChromaDB by its TBO ID."""
    try:
        collection = get_collection()
        results = collection.get(ids=[tbo_id], include=["metadatas"])
        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            return results["metadatas"][0]
    except Exception as e:
        logger.error(f"Failed to fetch destination by id {tbo_id}: {e}")
    return None
