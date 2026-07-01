from functools import lru_cache

from fastembed import TextEmbedding

from app.config import settings

# all-MiniLM-L6-v2 via ONNX runtime (fastembed).
# Produces identical 384-dim vectors to sentence-transformers but uses
# ~150MB RAM vs ~700MB for the PyTorch version — fits Render's free tier.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """Load the ONNX embedding model once and cache it."""
    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns a list of 384-dim vectors."""
    model = get_embedding_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
