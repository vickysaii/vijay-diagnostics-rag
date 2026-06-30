from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import chat

app = FastAPI(
    title="Vijay Diagnostics RAG Chatbot API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    # Safe to call repeatedly - only creates tables that don't already exist.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    """Quick check that the API process is alive (doesn't touch the DB)."""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/")
def root():
    return {"message": "Vijay Diagnostics RAG Chatbot API. See /docs for the API explorer."}
