"""
Ingestion script — run this manually whenever the knowledge base changes.

Usage (from the backend/ folder, with venv activated):
    python -m app.rag.ingest
"""
from pathlib import Path

from app.database import SessionLocal, engine, Base
from app.models import DocumentChunk
from app.rag.embeddings import embed_texts
from app.rag.text_splitter import split_markdown_into_chunks

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.md"
SOURCE_NAME = "knowledge_base.md"


def ingest():
    # Make sure all tables exist (safe to run repeatedly — it skips tables
    # that already exist).
    Base.metadata.create_all(bind=engine)

    text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    chunks = split_markdown_into_chunks(text)
    print(f"Split '{SOURCE_NAME}' into {len(chunks)} chunks.")

    contents = [c.content for c in chunks]
    print("Generating embeddings (first run downloads the model, ~80MB)...")
    embeddings = embed_texts(contents)

    db = SessionLocal()
    try:
        # Idempotency: wipe out previous chunks from this source before
        # re-inserting, so re-running this script after editing the
        # knowledge base doesn't leave stale duplicates behind.
        deleted = db.query(DocumentChunk).filter(DocumentChunk.source == SOURCE_NAME).delete()
        if deleted:
            print(f"Removed {deleted} old chunks from a previous run.")

        for chunk, embedding in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    source=SOURCE_NAME,
                    section=chunk.section,
                    content=chunk.content,
                    embedding=embedding,
                )
            )
        db.commit()
        print(f"Inserted {len(chunks)} chunks into document_chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
