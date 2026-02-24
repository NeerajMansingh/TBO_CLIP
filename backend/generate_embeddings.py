"""
generate_embeddings.py — One-time script to generate CLIP embeddings for all destinations.
Run once before starting the server. Output: destination_embeddings.json

Usage:
    cd backend/
    python generate_embeddings.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
DESTINATIONS_DIR = SCRIPT_DIR / "destinations"
OUTPUT_FILE = SCRIPT_DIR / "destination_embeddings.json"

# Maps destination folder name → TBO ID (must match fake_tbo.py)
DESTINATION_MAP = {
    "goa": {"tbo_id": "GOA_FAKE_001", "budget_tier": "budget"},
    "andaman": {"tbo_id": "ANDAMAN_FAKE_002", "budget_tier": "mid-range"},
    "kovalam": {"tbo_id": "KOVALAM_FAKE_003", "budget_tier": "budget"},
    "varkala": {"tbo_id": "VARKALA_FAKE_004", "budget_tier": "budget"},
    "pondicherry": {"tbo_id": "PONDICHERRY_FAKE_005", "budget_tier": "budget"},
    "manali": {"tbo_id": "MANALI_FAKE_006", "budget_tier": "mid-range"},
    "kasol": {"tbo_id": "KASOL_FAKE_007", "budget_tier": "budget"},
    "coorg": {"tbo_id": "COORG_FAKE_008", "budget_tier": "budget"},
    "munnar": {"tbo_id": "MUNNAR_FAKE_009", "budget_tier": "budget"},
    "darjeeling": {"tbo_id": "DARJEELING_FAKE_010", "budget_tier": "budget"},
    "spiti": {"tbo_id": "SPITI_FAKE_011", "budget_tier": "mid-range"},
    "jaipur": {"tbo_id": "JAIPUR_FAKE_012", "budget_tier": "mid-range"},
    "varanasi": {"tbo_id": "VARANASI_FAKE_013", "budget_tier": "budget"},
    "hampi": {"tbo_id": "HAMPI_FAKE_014", "budget_tier": "budget"},
    "mysore": {"tbo_id": "MYSORE_FAKE_015", "budget_tier": "budget"},
    "jodhpur": {"tbo_id": "JODHPUR_FAKE_016", "budget_tier": "budget"},
    "chikmagalur": {"tbo_id": "CHIKMAGALUR_FAKE_017", "budget_tier": "budget"},
    "wayanad": {"tbo_id": "WAYANAD_FAKE_018", "budget_tier": "budget"},
    "alleppey": {"tbo_id": "ALLEPPEY_FAKE_019", "budget_tier": "mid-range"},
    "jaisalmer": {"tbo_id": "JAISALMER_FAKE_020", "budget_tier": "budget"},
    "ziro": {"tbo_id": "ZIRO_FAKE_021", "budget_tier": "mid-range"},
    "udaipur": {"tbo_id": "UDAIPUR_FAKE_022", "budget_tier": "mid-range"},
    "leh": {"tbo_id": "LEH_FAKE_023", "budget_tier": "mid-range"},
    "rishikesh": {"tbo_id": "RISHIKESH_FAKE_024", "budget_tier": "budget"},
    "ooty": {"tbo_id": "OOTY_FAKE_025", "budget_tier": "budget"},
    "kerala_hills": {"tbo_id": "KERALA_BACKWATERS_FAKE_026", "budget_tier": "budget"},
    "shimla": {"tbo_id": "SHIMLA_FAKE_027", "budget_tier": "budget"},
    "mahabaleshwar": {"tbo_id": "MAHABALESHWAR_FAKE_028", "budget_tier": "budget"},
    "agra": {"tbo_id": "AGRA_FAKE_029", "budget_tier": "budget"},
    "shillong": {"tbo_id": "SHILLONG_FAKE_030", "budget_tier": "mid-range"},
}


def main():
    # Import here to avoid loading CLIP before necessary
    from clip_utils import embed_images_average, get_model

    logger.info("Loading CLIP model...")
    get_model()  # Pre-warm
    logger.info("CLIP model ready")

    results = {}
    processed = 0
    skipped = 0

    for dest_folder, meta in DESTINATION_MAP.items():
        dest_dir = DESTINATIONS_DIR / dest_folder

        if not dest_dir.exists():
            logger.warning(f"[SKIP] No folder found for: {dest_folder}")
            skipped += 1
            continue

        # Load all available images (from new 20 image scrape)
        image_files = sorted(
            [f for f in dest_dir.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        )

        if not image_files:
            logger.warning(f"[SKIP] No images found in: {dest_dir}")
            skipped += 1
            continue

        logger.info(f"Processing {dest_folder} ({len(image_files)} images)...")

        try:
            images = [Image.open(f).convert("RGB") for f in image_files]
            avg_embedding = embed_images_average(images)

            # Use the first image as the representative photo
            representative_photo = f"destinations/{dest_folder}/{image_files[0].name}"

            results[dest_folder] = {
                "embedding": avg_embedding,
                "budget_tier": meta["budget_tier"],
                "tbo_id": meta["tbo_id"],
                "photo": representative_photo,
                "num_images_used": len(image_files),
            }

            processed += 1
            logger.info(f"  ✓ {dest_folder}: embedding shape {len(avg_embedding)}, photo={representative_photo}")

        except Exception as e:
            logger.error(f"  ✗ Failed to process {dest_folder}: {e}")
            skipped += 1

    # Save to JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n{'='*50}")
    logger.info(f"Embeddings generated: {processed} destinations")
    logger.info(f"Skipped: {skipped} destinations")
    logger.info(f"Output saved to: {OUTPUT_FILE}")

    # Validation: verify first embedding has 512 dimensions
    if results:
        first_key = next(iter(results))
        emb_len = len(results[first_key]["embedding"])
        logger.info(f"Embedding dimension check: {first_key} → {emb_len} dims (expected 512)")
        if emb_len != 512:
            logger.error("WARNING: Unexpected embedding dimension!")
            sys.exit(1)
    
    logger.info("✓ Embedding generation complete!")


if __name__ == "__main__":
    main()
