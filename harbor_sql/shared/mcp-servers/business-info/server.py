import json
import logging
import os
import threading
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("business-info")

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
BUSINESS_INFO_PATH = DATA_DIR / "business_info.json"
CHROMA_PATH = "/tmp/chromadb"
COLLECTION_NAME = "business_info"
N_RESULTS = 5

_collection_lock = threading.Lock()
_embedding_lock = threading.Lock()
_embedding_function = None
_collection_cache = {}
_database_name = None


def _get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        with _embedding_lock:
            if _embedding_function is None:
                _embedding_function = SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
    return _embedding_function


def _warm_embedding_model() -> None:
    try:
        embedding_fn = _get_embedding_function()
        embedding_fn(["business info warmup"])
        logger.info("business-info MCP: embedding model warmup complete")
    except Exception as exc:
        logger.warning("business-info MCP warmup failed: %s", exc)


def _get_collection(chroma_path: str, collection_name: str):
    key = (str(Path(chroma_path).resolve()), collection_name)
    with _collection_lock:
        cached = _collection_cache.get(key)
        if cached is not None:
            return cached
        client = chromadb.PersistentClient(path=key[0])
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=_get_embedding_function(),
        )
        _collection_cache[key] = collection
        return collection


def initialize_chromadb() -> None:
    global _database_name
    if not BUSINESS_INFO_PATH.exists():
        raise FileNotFoundError(f"Business info file not found: {BUSINESS_INFO_PATH}")

    data = json.loads(BUSINESS_INFO_PATH.read_text())
    _database_name = data["database_name"]
    business_info = data["business_info"]
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)

    collection = _get_collection(CHROMA_PATH, COLLECTION_NAME)
    try:
        # Ensure deterministic content for every container start.
        existing = collection.get(limit=1)
        if existing and existing.get("ids"):
            ids = collection.get().get("ids", [])
            if ids:
                collection.delete(ids=ids)
    except Exception:
        pass
    collection.add(
        documents=business_info,
        metadatas=[{"database_name": _database_name} for _ in business_info],
        ids=[f"bi_{i}" for i in range(len(business_info))],
    )
    logger.info("Loaded %s business info entries", len(business_info))


@mcp.tool()
def get_business_info(database_name: str, search_string: str) -> str:
    """Retrieves UP TO the top 5 semantically similar results to the search string from a knowledge base containing business logic, rules, definitions, etc."""
    if not database_name:
        return "Error querying knowledge base: Missing database_name"
    if not search_string:
        return "Error querying knowledge base: Missing search_string"
    try:
        collection = _get_collection(CHROMA_PATH, COLLECTION_NAME)
        results = collection.query(
            query_texts=[search_string],
            n_results=N_RESULTS,
            where={"database_name": database_name},
        )
        docs = []
        if results and results.get("documents") and results["documents"]:
            docs = results["documents"][0] or []
        if not docs:
            return f"No business information found matching '{search_string}'."
        infos = [f"{i + 1}. {doc.strip()}" for i, doc in enumerate(docs)]
        return "\n".join(infos)
    except Exception as e:
        logger.exception("business-info MCP query failed")
        return f"Error querying knowledge base: {e}"


if __name__ == "__main__":
    _warm_embedding_model()
    initialize_chromadb()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
