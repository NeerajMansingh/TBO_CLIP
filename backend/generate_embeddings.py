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
    "andaman": {"tbo_id": "ANDAMAN_FAKE_002", "budget_tier": "premium"},
    "kovalam": {"tbo_id": "KOVALAM_FAKE_003", "budget_tier": "budget"},
    "varkala": {"tbo_id": "VARKALA_FAKE_004", "budget_tier": "mid-range"},
    "pondicherry": {"tbo_id": "PONDICHERRY_FAKE_005", "budget_tier": "budget"},
    "manali": {"tbo_id": "MANALI_FAKE_006", "budget_tier": "premium"},
    "kasol": {"tbo_id": "KASOL_FAKE_007", "budget_tier": "budget"},
    "coorg": {"tbo_id": "COORG_FAKE_008", "budget_tier": "premium"},
    "munnar": {"tbo_id": "MUNNAR_FAKE_009", "budget_tier": "budget"},
    "darjeeling": {"tbo_id": "DARJEELING_FAKE_010", "budget_tier": "mid-range"},
    "spiti": {"tbo_id": "SPITI_FAKE_011", "budget_tier": "budget"},
    "jaipur": {"tbo_id": "JAIPUR_FAKE_012", "budget_tier": "premium"},
    "varanasi": {"tbo_id": "VARANASI_FAKE_013", "budget_tier": "budget"},
    "hampi": {"tbo_id": "HAMPI_FAKE_014", "budget_tier": "premium"},
    "mysore": {"tbo_id": "MYSORE_FAKE_015", "budget_tier": "budget"},
    "jodhpur": {"tbo_id": "JODHPUR_FAKE_016", "budget_tier": "mid-range"},
    "chikmagalur": {"tbo_id": "CHIKMAGALUR_FAKE_017", "budget_tier": "budget"},
    "wayanad": {"tbo_id": "WAYANAD_FAKE_018", "budget_tier": "premium"},
    "alleppey": {"tbo_id": "ALLEPPEY_FAKE_019", "budget_tier": "budget"},
    "jaisalmer": {"tbo_id": "JAISALMER_FAKE_020", "budget_tier": "premium"},
    "ziro": {"tbo_id": "ZIRO_FAKE_021", "budget_tier": "budget"},
    "udaipur": {"tbo_id": "UDAIPUR_FAKE_022", "budget_tier": "mid-range"},
    "leh": {"tbo_id": "LEH_FAKE_023", "budget_tier": "budget"},
    "rishikesh": {"tbo_id": "RISHIKESH_FAKE_024", "budget_tier": "premium"},
    "ooty": {"tbo_id": "OOTY_FAKE_025", "budget_tier": "budget"},
    "kerala_hills": {"tbo_id": "KERALA_HILLS_FAKE_026", "budget_tier": "premium"},
    "shimla": {"tbo_id": "SHIMLA_FAKE_027", "budget_tier": "budget"},
    "mahabaleshwar": {"tbo_id": "MAHABALESHWAR_FAKE_028", "budget_tier": "mid-range"},
    "agra": {"tbo_id": "AGRA_FAKE_029", "budget_tier": "budget"},
    "shillong": {"tbo_id": "SHILLONG_FAKE_030", "budget_tier": "premium"},
    "gulmarg": {"tbo_id": "GULMARG_FAKE_031", "budget_tier": "budget"},
    "tawang": {"tbo_id": "TAWANG_FAKE_032", "budget_tier": "premium"},
    "kutch": {"tbo_id": "KUTCH_FAKE_033", "budget_tier": "budget"},
    "khajuraho": {"tbo_id": "KHAJURAHO_FAKE_034", "budget_tier": "mid-range"},
    "dalhousie": {"tbo_id": "DALHOUSIE_FAKE_035", "budget_tier": "budget"},
    "auli": {"tbo_id": "AULI_FAKE_036", "budget_tier": "premium"},
    "kodaikanal": {"tbo_id": "KODAIKANAL_FAKE_037", "budget_tier": "budget"},
    "pushkar": {"tbo_id": "PUSHKAR_FAKE_038", "budget_tier": "premium"},
    "mount_abu": {"tbo_id": "MOUNT_ABU_FAKE_039", "budget_tier": "budget"},
    "gokarna": {"tbo_id": "GOKARNA_FAKE_040", "budget_tier": "mid-range"},
    "majuli": {"tbo_id": "MAJULI_FAKE_041", "budget_tier": "budget"},
    "lonavala": {"tbo_id": "LONAVALA_FAKE_042", "budget_tier": "premium"},
    "srinagar": {"tbo_id": "SRINAGAR_FAKE_043", "budget_tier": "budget"},
    "pahalgam": {"tbo_id": "PAHALGAM_FAKE_044", "budget_tier": "premium"},
    "ranthambore": {"tbo_id": "RANTHAMBORE_FAKE_045", "budget_tier": "budget"},
    "kaziranga": {"tbo_id": "KAZIRANGA_FAKE_046", "budget_tier": "mid-range"},
    "sunderbans": {"tbo_id": "SUNDERBANS_FAKE_047", "budget_tier": "budget"},
    "mathura": {"tbo_id": "MATHURA_FAKE_048", "budget_tier": "premium"},
    "kanyakumari": {"tbo_id": "KANYAKUMARI_FAKE_049", "budget_tier": "budget"},
    "rameshwaram": {"tbo_id": "RAMESHWARAM_FAKE_050", "budget_tier": "premium"},
    "tirupati": {"tbo_id": "TIRUPATI_FAKE_051", "budget_tier": "budget"},
    "madurai": {"tbo_id": "MADURAI_FAKE_052", "budget_tier": "mid-range"},
    "nainital": {"tbo_id": "NAINITAL_FAKE_053", "budget_tier": "budget"},
    "mussoorie": {"tbo_id": "MUSSOORIE_FAKE_054", "budget_tier": "premium"},
    "lansdowne": {"tbo_id": "LANSDOWNE_FAKE_055", "budget_tier": "budget"},
    "ranikhet": {"tbo_id": "RANIKHET_FAKE_056", "budget_tier": "premium"},
    "almora": {"tbo_id": "ALMORA_FAKE_057", "budget_tier": "budget"},
    "kausani": {"tbo_id": "KAUSANI_FAKE_058", "budget_tier": "mid-range"},
    "dharamshala": {"tbo_id": "DHARAMSHALA_FAKE_059", "budget_tier": "budget"},
    "bir_billing": {"tbo_id": "BIR_BILLING_FAKE_060", "budget_tier": "premium"},
    "khajjiar": {"tbo_id": "KHAJJIAR_FAKE_061", "budget_tier": "budget"},
    "kinnaur": {"tbo_id": "KINNAUR_FAKE_062", "budget_tier": "premium"},
    "lahaul": {"tbo_id": "LAHAUL_FAKE_063", "budget_tier": "budget"},
    "nubra_valley": {"tbo_id": "NUBRA_VALLEY_FAKE_064", "budget_tier": "mid-range"},
    "pangong_tso": {"tbo_id": "PANGONG_TSO_FAKE_065", "budget_tier": "budget"},
    "tso_moriri": {"tbo_id": "TSO_MORIRI_FAKE_066", "budget_tier": "premium"},
    "kargil": {"tbo_id": "KARGIL_FAKE_067", "budget_tier": "budget"},
    "sonamarg": {"tbo_id": "SONAMARG_FAKE_068", "budget_tier": "premium"},
    "amritsar": {"tbo_id": "AMRITSAR_FAKE_069", "budget_tier": "budget"},
    "chandigarh": {"tbo_id": "CHANDIGARH_FAKE_070", "budget_tier": "mid-range"},
    "haridwar": {"tbo_id": "HARIDWAR_FAKE_071", "budget_tier": "budget"},
    "jim_corbett": {"tbo_id": "JIM_CORBETT_FAKE_072", "budget_tier": "premium"},
    "bandhavgarh": {"tbo_id": "BANDHAVGARH_FAKE_073", "budget_tier": "budget"},
    "kanha": {"tbo_id": "KANHA_FAKE_074", "budget_tier": "premium"},
    "gir": {"tbo_id": "GIR_FAKE_075", "budget_tier": "budget"},
    "somnath": {"tbo_id": "SOMNATH_FAKE_076", "budget_tier": "mid-range"},
    "dwarka": {"tbo_id": "DWARKA_FAKE_077", "budget_tier": "budget"},
    "ajmer": {"tbo_id": "AJMER_FAKE_078", "budget_tier": "premium"},
    "bikaner": {"tbo_id": "BIKANER_FAKE_079", "budget_tier": "budget"},
    "chittorgarh": {"tbo_id": "CHITTORGARH_FAKE_080", "budget_tier": "premium"},
    "kumbhalgarh": {"tbo_id": "KUMBHALGARH_FAKE_081", "budget_tier": "budget"},
    "orchha": {"tbo_id": "ORCHHA_FAKE_082", "budget_tier": "mid-range"},
    "gwalior": {"tbo_id": "GWALIOR_FAKE_083", "budget_tier": "budget"},
    "sanchi": {"tbo_id": "SANCHI_FAKE_084", "budget_tier": "premium"},
    "bhimbetka": {"tbo_id": "BHIMBETKA_FAKE_085", "budget_tier": "budget"},
    "mandu": {"tbo_id": "MANDU_FAKE_086", "budget_tier": "premium"},
    "ujjain": {"tbo_id": "UJJAIN_FAKE_087", "budget_tier": "budget"},
    "pachmarhi": {"tbo_id": "PACHMARHI_FAKE_088", "budget_tier": "mid-range"},
    "jabalpur": {"tbo_id": "JABALPUR_FAKE_089", "budget_tier": "budget"},
    "chitrakoot": {"tbo_id": "CHITRAKOOT_FAKE_090", "budget_tier": "premium"},
    "bodh_gaya": {"tbo_id": "BODH_GAYA_FAKE_091", "budget_tier": "budget"},
    "nalanda": {"tbo_id": "NALANDA_FAKE_092", "budget_tier": "premium"},
    "konark": {"tbo_id": "KONARK_FAKE_093", "budget_tier": "budget"},
    "puri": {"tbo_id": "PURI_FAKE_094", "budget_tier": "mid-range"},
    "bhubaneswar": {"tbo_id": "BHUBANESWAR_FAKE_095", "budget_tier": "budget"},
    "chilika": {"tbo_id": "CHILIKA_FAKE_096", "budget_tier": "premium"},
    "araku": {"tbo_id": "ARAKU_FAKE_097", "budget_tier": "budget"},
    "belur": {"tbo_id": "BELUR_FAKE_098", "budget_tier": "premium"},
    "badami": {"tbo_id": "BADAMI_FAKE_099", "budget_tier": "budget"},
    "gokak": {"tbo_id": "GOKAK_FAKE_100", "budget_tier": "mid-range"},
}


def main():
    # Import here to avoid loading CLIP before necessary
    from clip_utils import get_model
    import torch

    logger.info("Loading CLIP model...")
    model = get_model()  # Pre-warm
    logger.info("CLIP model ready")

    # Load existing results if they exist to allow resume
    results = {}
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r") as f:
                results = json.load(f)
            logger.info(f"Loaded {len(results)} existing embeddings from {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Failed to load existing embeddings: {e}")

    processed = 0
    skipped = 0
    
    # Process folders one by one
    all_folders = list(DESTINATION_MAP.keys())
    total_folders = len(all_folders)
    
    for idx, dest_folder in enumerate(all_folders):
        # Skip if already in results
        if dest_folder in results:
            continue
            
        meta = DESTINATION_MAP[dest_folder]
        dest_dir = DESTINATIONS_DIR / dest_folder

        if not dest_dir.exists():
            logger.warning(f"[SKIP] No folder found for: {dest_folder}")
            skipped += 1
            continue

        # Load all available images
        image_files = sorted(
            [f for f in dest_dir.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        )

        if not image_files:
            logger.warning(f"[SKIP] No images found in: {dest_dir}")
            skipped += 1
            continue

        logger.info(f"[{idx+1}/{total_folders}] Processing {dest_folder} ({len(image_files)} images)...")

        try:
            # Memory efficient approach: embed images one by one
            image_embeddings = []
            
            for f in image_files:
                try:
                    with Image.open(f) as img:
                        img_rgb = img.convert("RGB")
                        # Get individual embedding
                        emb = model.encode(img_rgb, show_progress_bar=False)
                        image_embeddings.append(emb)
                except Exception as img_err:
                    logger.warning(f"  ! Error loading {f.name}: {img_err}")

            if not image_embeddings:
                logger.warning(f"  ! No valid images could be embedded for {dest_folder}")
                skipped += 1
                continue

            # Average and normalize
            avg_embedding = np.mean(image_embeddings, axis=0)
            norm = np.linalg.norm(avg_embedding)
            if norm > 0:
                avg_embedding = avg_embedding / norm
            
            avg_list = avg_embedding.tolist()

            # Use the first image as the representative photo
            representative_photo = f"destinations/{dest_folder}/{image_files[0].name}"

            results[dest_folder] = {
                "embedding": avg_list,
                "budget_tier": meta["budget_tier"],
                "tbo_id": meta["tbo_id"],
                "photo": representative_photo,
                "num_images_used": len(image_embeddings),
            }

            processed += 1
            logger.info(f"  ✓ {dest_folder}: {len(image_embeddings)} images used")

            # Save progress after EACH destination (batch-wise incremental saving)
            with open(OUTPUT_FILE, "w") as f:
                json.dump(results, f, indent=2)

        except Exception as e:
            logger.error(f"  ✗ Failed to process {dest_folder}: {e}")
            skipped += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Total processed: {len(results)} destinations")
    logger.info(f"New embeddings added: {processed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Final output: {OUTPUT_FILE}")

    if results:
        first_key = next(iter(results))
        emb_len = len(results[first_key]["embedding"])
        logger.info(f"Embedding dimension check: {first_key} → {emb_len} dims")
    
    logger.info("✓ Batch processing and embedding complete!")


if __name__ == "__main__":
    main()
