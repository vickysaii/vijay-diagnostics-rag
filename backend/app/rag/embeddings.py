import os
import time

import requests

from app.config import settings

# HuggingFace Inference API endpoint for our embedding model.
# Runs the model on HF's servers instead of locally — no PyTorch/GPU needed,
# so Render's free 512MB instance can handle it comfortably.
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"


def _hf_headers() -> dict:
    token = settings.HF_API_TOKEN
    if not token:
        raise ValueError("HF_API_TOKEN is not set. Add it to your .env file and Render environment variables.")
    return {"Authorization": f"Bearer {token}"}


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts via the HuggingFace Inference API.
    Returns a list of 384-dimensional embedding vectors.
    """
    response = requests.post(
        HF_API_URL,
        headers=_hf_headers(),
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=60,
    )

    if response.status_code == 503:
        # Model is loading on HF's side — wait and retry once
        time.sleep(20)
        response = requests.post(
            HF_API_URL,
            headers=_hf_headers(),
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=60,
        )

    response.raise_for_status()
    return response.json()


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
