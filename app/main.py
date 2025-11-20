from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_chat import router as chat_router
from app.agents.tooling import ensure_agentic_tooling_ready
from app.retrieval.ingest import ingest_all_pdfs
import os

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "annual_reports"

app = FastAPI()


def ensure_chroma_ready():
    """Run ingestion only if DB is missing or empty."""
    from chromadb import PersistentClient

    if not os.path.exists(CHROMA_PATH):
        print("No Chroma DB: running ingestion...")
        ingest_all_pdfs()
        return

    client = PersistentClient(CHROMA_PATH)
    try:
        coll = client.get_collection(COLLECTION_NAME)
        if coll.count() == 0:
            print("Empty collection: running ingestion...")
            ingest_all_pdfs()
        else:
            print(f"Chroma is ready ({coll.count()} documents)")
    except Exception:
        print("Collection missing: running ingestion...")
        ingest_all_pdfs()


@app.on_event("startup")
def startup_event():
    ensure_chroma_ready()
    ensure_agentic_tooling_ready()


# 1) Register API routes
app.include_router(chat_router, prefix="/api")

# 2) Serve frontend
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="static")
