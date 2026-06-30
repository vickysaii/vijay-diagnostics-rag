from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocumentChunk
from app.rag.embeddings import embed_query


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    distance: float  # cosine distance: 0 = identical meaning, higher = less related


def retrieve_relevant_chunks(db: Session, query: str, top_k: int = 6) -> list[RetrievedChunk]:
    """
    Embeds the query, finds the top_k closest chunks via pgvector cosine
    distance, then filters out any that are too weak to be genuinely
    relevant (controlled by settings.MAX_RELEVANT_DISTANCE).

    Cosine similarity search always returns *something* - even for a
    completely off-topic question like "what's the weather today", it'll
    return the 6 "least dissimilar" chunks. The distance filter is what lets
    the chatbot say "I don't have that information" instead of confidently
    answering from irrelevant context.
    """
    query_embedding = embed_query(query)
    distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

    rows = db.query(DocumentChunk, distance_col).order_by(distance_col).limit(top_k).all()
    results = [RetrievedChunk(chunk=chunk, distance=distance) for chunk, distance in rows]

    return [r for r in results if r.distance <= settings.MAX_RELEVANT_DISTANCE]
