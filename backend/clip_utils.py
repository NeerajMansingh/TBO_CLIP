import logging
import os
import torch
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)

# Constants
CLIP_MODEL_NAME = 'sentence-transformers/clip-ViT-B-32'

_model = None
_device = None

def get_model():
    """Lazy loads the CLIP model to memory."""
    global _model, _device
    if _model is None:
        logger.info(f"Loading CLIP model: {CLIP_MODEL_NAME}")
        
        # Decide device
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        # If running on macOS with M-series chips, can use mps
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            _device = "mps"
            
        logger.info(f"Use pytorch device_name: {_device}")
        
        # Download the model explicitly ignoring large .bin files to use safetensors
        logger.info("Downloading models while ignoring *.bin files to prevent stalls...")
        model_path = snapshot_download(
            repo_id=CLIP_MODEL_NAME, 
            ignore_patterns=["*.bin", "*.h5", "*.msgpack"]
        )
        
        # Load the visual/text matching model from the local path
        _model = SentenceTransformer(model_path)
        _model.to(_device)
        
    return _model

def get_image_embedding(image: Image.Image) -> list[float]:
    """Generates an embedding vector for a single image."""
    model = get_model()
    # SentenceTransformer handles PIL Images directly for CLIP models
    embedding = model.encode(image, show_progress_bar=False)
    # Convert numpy array to list of floats for ChromaDB
    # We ensure it's a 1D array of floats
    return embedding.tolist()

def embed_images_average(images: list[Image.Image]) -> list[float]:
    """Generates an average embedding for a list of images."""
    if not images:
        return []
    
    model = get_model()
    # Encode all images in batch
    embeddings = model.encode(images, show_progress_bar=False)
    
    # Average the embeddings along the 0th axis
    avg_embedding = np.mean(embeddings, axis=0)
    
    # L2 Normalize the averaged vector
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding = avg_embedding / norm
        
    return avg_embedding.tolist()

def get_text_embedding(text: str) -> list[float]:
    """Generates an embedding vector for text."""
    model = get_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()

def get_image_vibes(image: Image.Image) -> list[str]:
    """Zero-shot classification to get aesthetic/vibe keywords for an image."""
    model = get_model()
    
    candidate_labels = [
        "mountainous", "beachy", "historic", "romantic", "adventurous", 
        "peaceful", "cultural", "nature", "vibrant", "chill",
        "forest", "desert", "snowy", "urban", "spiritual",
        "luxury", "budget", "family-friendly", "solo-traveler", 
        "architecture", "wildlife", "foodie"
    ]
    
    # We encode the image and all candidates, then compute cosine similarity
    img_emb = model.encode(image)
    text_embs = model.encode(candidate_labels)
    
    # Compute cosine similarities
    similarities = np.dot(text_embs, img_emb) / (np.linalg.norm(text_embs, axis=1) * np.linalg.norm(img_emb))
    
    # Get top 3 indices
    top_indices = np.argsort(similarities)[-3:][::-1]
    
    return [candidate_labels[i] for i in top_indices]
