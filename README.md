# Vijay Diagnostics RAG Chatbot — Phase 1: Project Setup

This is Phase 1 of 6. At the end of this phase you'll have a FastAPI server
running locally with a Postgres + pgvector database ready to receive data.
No RAG logic yet — that's Phase 2.

## Prerequisites
- Python 3.11+ installed
- Docker Desktop installed and running (for Postgres)
- VS Code with the "Python" extension installed

## Step 1 — Open the project in VS Code
Unzip this folder, then in VS Code: File → Open Folder → select `vijay-diagnostics-rag`.

## Step 2 — Create a virtual environment
Open a terminal in VS Code (`` Ctrl+` ``) and run, from the `backend` folder:

```bash
cd backend
python3 -m venv venv
```

Activate it:
- **Mac/Linux**: `source venv/bin/activate`
- **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`

You should see `(venv)` appear at the start of your terminal prompt.

VS Code may also pop up a prompt: "Select Python Interpreter" — choose the one
inside `venv`.

## Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```
This installs FastAPI, SQLAlchemy, LangChain, sentence-transformers, etc.
It'll take a few minutes the first time (sentence-transformers pulls in PyTorch).

## Step 4 — Start Postgres (with pgvector) via Docker
Still inside `backend/`:
```bash
docker compose up -d
```
This pulls the `pgvector/pgvector:pg16` image and starts Postgres on port 5432,
with the pgvector extension already installed in the image.

Check it's running: `docker ps` — you should see `vijay_postgres` as healthy.

## Step 5 — Create your `.env` file
```bash
cp .env.example .env
```
Open `.env` and fill in your `GROQ_API_KEY`- GROQ_API_KEY=your_groq_api_key_here (get a free one at
https://console.groq.com/keys). You can leave `DATABASE_URL` as-is — it
already matches the docker-compose settings.

## Step 6 — Enable the pgvector extension inside the database
The image has pgvector installed, but each database still needs the extension
turned on once:

```bash
docker exec -it vijay_postgres psql -U vijay_user -d vijay_diagnostics -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Step 7 — Run the API
```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs in your browser — you should see the FastAPI
interactive docs (Swagger UI) with a `/health` endpoint. Try it — it should
return `{"status": "ok", "env": "development"}`.

## ✅ Checkpoint
If `/health` returns OK and `docker ps` shows Postgres healthy, Phase 1 is done.
Reply and we'll move to Phase 2: loading the Vijay Diagnostics knowledge base
(test catalog, prep instructions, home collection policy, branches) and
building the ingestion pipeline that chunks + embeds + stores it in pgvector.

## Project structure so far
```
vijay-diagnostics-rag/
└── backend/
    ├── app/
    │   ├── main.py        # FastAPI app + /health endpoint
    │   ├── config.py      # settings loaded from .env
    │   ├── database.py    # SQLAlchemy engine/session
    │   ├── models.py      # DocumentChunk, ChatSession, ChatMessage tables
    │   ├── schemas.py      # Pydantic request/response models
    │   ├── rag/            # (Phase 2/3: ingestion + retrieval logic goes here)
    │   └── data/            # (Phase 2: knowledge base source files go here)
    ├── requirements.txt
    ├── docker-compose.yml  # Postgres + pgvector for local dev
    ├── .env.example
    └── README.md (this file)
```
