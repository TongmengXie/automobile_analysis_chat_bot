from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from chromadb import PersistentClient

from app.config import OPENAI_API_KEY, EMBEDDING_MODEL

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "annual_reports"


def get_retriever(filters=None):
    """Return a metadata-aware retriever."""

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    client = PersistentClient(path=CHROMA_PATH)

    store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    search_kwargs = {"k": 5}
    if filters:
        search_kwargs["filter"] = filters

    return store.as_retriever(search_kwargs=search_kwargs)
