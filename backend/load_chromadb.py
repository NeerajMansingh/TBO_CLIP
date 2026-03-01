"""
load_chromadb.py — One-time script to load destination embeddings into ChromaDB.
Run after generate_embeddings.py has created destination_embeddings.json.

Usage:
    cd backend/
    python load_chromadb.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
EMBEDDINGS_FILE = SCRIPT_DIR / "destination_embeddings.json"

# Human-readable names for each destination folder
DESTINATION_NAMES = {
    "goa": "Goa",
    "andaman": "Andaman Islands",
    "kovalam": "Kovalam",
    "varkala": "Varkala",
    "pondicherry": "Pondicherry",
    "manali": "Manali",
    "kasol": "Kasol",
    "coorg": "Coorg",
    "munnar": "Munnar",
    "darjeeling": "Darjeeling",
    "spiti": "Spiti Valley",
    "jaipur": "Jaipur",
    "varanasi": "Varanasi",
    "hampi": "Hampi",
    "mysore": "Mysore",
    "jodhpur": "Jodhpur",
    "chikmagalur": "Chikmagalur",
    "wayanad": "Wayanad",
    "alleppey": "Alleppey (Alappuzha)",
    "jaisalmer": "Jaisalmer",
    "ziro": "Ziro Valley",
    "udaipur": "Udaipur",
    "leh": "Leh-Ladakh",
    "rishikesh": "Rishikesh",
    "ooty": "Ooty",
    "kerala_hills": "Kerala Hill Stations",
    "shimla": "Shimla",
    "mahabaleshwar": "Mahabaleshwar",
    "agra": "Agra",
    "shillong": "Shillong",
}

# Price per person (must match fake_tbo.py)
DESTINATION_PRICES = {
    "goa": 18000, "andaman": 28000, "kovalam": 14000, "varkala": 12000,
    "pondicherry": 14000, "manali": 22000, "kasol": 10000, "coorg": 19000,
    "munnar": 16000, "darjeeling": 18000, "spiti": 25000, "jaipur": 20000,
    "varanasi": 12000, "hampi": 11000, "mysore": 15000, "jodhpur": 17000,
    "chikmagalur": 14000, "wayanad": 15000, "alleppey": 20000, "jaisalmer": 16000,
    "ziro": 22000, "udaipur": 24000, "leh": 42000, "rishikesh": 13000,
    "ooty": 13000, "kerala_hills": 17000, "shimla": 17000, "mahabaleshwar": 14000,
    "agra": 15000, "shillong": 20000,
    
    # Major Cities
    "delhi": 18000, "mumbai": 22000, "bangalore": 16000, 
    "hyderabad": 15000, "kolkata": 14000, "chennai": 15000,
    
    # Northeast Additions
    "cherrapunji": 12000, "dawki": 10000, "mawsynram": 10000,
    "gangtok": 18000, "pelling": 16000,
}


def main():
    from chromadb_utils import add_destination, get_collection, get_collection_count

    if not EMBEDDINGS_FILE.exists():
        logger.error(f"Embeddings file not found: {EMBEDDINGS_FILE}")
        logger.error("Run generate_embeddings.py first!")
        sys.exit(1)

    logger.info(f"Loading embeddings from: {EMBEDDINGS_FILE}")

    with open(EMBEDDINGS_FILE) as f:
        embeddings_data = json.load(f)

    logger.info(f"Found {len(embeddings_data)} destinations in embeddings file")

    # Clear existing collection to avoid duplicates on re-runs
    import chromadb
    from chromadb_utils import CHROMA_STORE_PATH, COLLECTION_NAME, get_client

    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Cleared existing '{COLLECTION_NAME}' collection")
    except Exception:
        pass  # Collection didn't exist yet

    loaded = 0
    failed = 0

    for dest_folder, data in embeddings_data.items():
        destination_name = DESTINATION_NAMES.get(dest_folder, dest_folder.title())
        price = DESTINATION_PRICES.get(dest_folder, 20000)

        try:
            embedding = data["embedding"]

            # Validate embedding dimension
            if len(embedding) != 512:
                logger.warning(f"Skipping {dest_folder}: unexpected embedding dim {len(embedding)}")
                failed += 1
                continue

            add_destination(
                destination_name=destination_name,
                embedding=embedding,
                tbo_id=data["tbo_id"],
                budget_tier=data["budget_tier"],
                photo_path=data["photo"],
                price_per_person=price,
            )

            loaded += 1
            logger.info(f"  ✓ Loaded: {destination_name} ({data['tbo_id']})")

        except Exception as e:
            logger.error(f"  ✗ Failed to load {dest_folder}: {e}")
            failed += 1

    total_in_db = get_collection_count()

    logger.info(f"\n{'='*50}")
    logger.info(f"Destinations loaded into ChromaDB: {loaded}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total in ChromaDB collection: {total_in_db}")

    # Quick test query: generate a random vector and find 3 closest
    logger.info("\nRunning test query with random embedding...")
    test_embedding = np.random.randn(512).astype(np.float32)
    test_embedding = test_embedding / np.linalg.norm(test_embedding)

    from chromadb_utils import query_similar_destinations
    test_results = query_similar_destinations(
        query_embedding=test_embedding,
        budget_tier="mid-range",
        n_results=3,
    )

    logger.info(f"Test query returned {len(test_results)} results:")
    for i, r in enumerate(test_results, 1):
        logger.info(f"  {i}. {r['destination']} (score: {r['similarity_score']:.3f})")

    logger.info("\n✓ ChromaDB loading complete!")


if __name__ == "__main__":
    main()
