from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage, ChatSession
from app.rag.chain import LLMGenerationError, generate_answer
from app.rag.retriever import retrieve_relevant_chunks
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HistoryMessage,
    HistoryResponse,
    SourceChunk,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    # --- 1. Get or create the chat session ---
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession()
        db.add(session)
        db.commit()
        db.refresh(session)

    # --- 2. Load prior conversation history for this session ---
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    # --- 3. Persist the user's message ---
    db.add(ChatMessage(session_id=session.id, role="user", content=request.message.strip()))
    db.commit()

    # --- 4. Retrieve relevant knowledge base chunks (already filtered by relevance) ---
    try:
        retrieved = retrieve_relevant_chunks(db, request.message, top_k=6)
    except Exception as e:
        # Covers DB issues or embedding-model failures - fail loudly with a
        # clean 503 instead of an unhandled 500 with a raw traceback.
        raise HTTPException(status_code=503, detail=f"Retrieval failed: {e}") from e

    # --- 5. Generate the grounded answer via the LLM ---
    try:
        answer = generate_answer(request.message, retrieved, history)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # --- 6. Persist the assistant's reply ---
    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer))
    db.commit()

    return ChatResponse(
        session_id=session.id,
        answer=answer,
        sources=[
            SourceChunk(source=r.chunk.source, section=r.chunk.section, content=r.chunk.content)
            for r in retrieved
        ],
    )


@router.get("/chat/{session_id}/history", response_model=HistoryResponse)
def get_history(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return HistoryResponse(
        session_id=session.id,
        messages=[
            HistoryMessage(role=m.role, content=m.content, created_at=m.created_at)
            for m in messages
        ],
    )
