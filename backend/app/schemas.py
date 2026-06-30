import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None  # if None, a new session is created


class SourceChunk(BaseModel):
    source: str
    section: str | None = None
    content: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    sources: list[SourceChunk] = []


class HistoryMessage(BaseModel):
    role: str
    content: str
    created_at: datetime


class HistoryResponse(BaseModel):
    session_id: uuid.UUID
    messages: list[HistoryMessage]
