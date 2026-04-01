import argparse
import json
import logging
import threading
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_collection_lock = threading.Lock()
_embedding_lock = threading.Lock()
_embedding_function = None
_collection_cache = {}


def _get_embedding_function():
    """Lazily construct a single embedding model per server process."""
    global _embedding_function
    if _embedding_function is None:
        with _embedding_lock:
            if _embedding_function is None:
                _embedding_function = SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
    return _embedding_function


def _warm_embedding_model() -> None:
    """Force model initialization at server startup to avoid first-query stalls."""
    try:
        embedding_fn = _get_embedding_function()
        # Trigger eager model load if the embedding function is callable.
        embedding_fn(["business info warmup"])
        logger.info("get_business_info server: embedding model warmup complete")
    except Exception as exc:
        # Keep server alive even if warmup fails; query requests will surface errors.
        logger.warning("get_business_info server warmup failed: %s", exc)


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


def _parse_common_payload(data: dict):
    chroma_path = data.get("chroma_path")
    collection_name = data.get("collection_name", "business_info")
    if not chroma_path:
        raise ValueError("Missing chroma_path")
    return chroma_path, collection_name


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.get_json(silent=True) or {}
        database_name = data.get("database_name")
        search_string = data.get("search_string")
        if not database_name:
            return jsonify({"error": "Missing database_name"}), 400
        if not search_string:
            return jsonify({"error": "Missing search_string"}), 400
        chroma_path, collection_name = _parse_common_payload(data)
        n_results = int(data.get("n_results", 5))
        if n_results < 1:
            return jsonify({"error": "n_results must be >= 1"}), 400

        collection = _get_collection(chroma_path, collection_name)
        results = collection.query(
            query_texts=[search_string],
            n_results=n_results,
            where={"database_name": database_name},
        )
        docs = []
        if results and results.get("documents") and results["documents"]:
            docs = results["documents"][0] or []
        return jsonify({"documents": docs})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("get_business_info server query failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/view_all", methods=["POST"])
def view_all():
    try:
        data = request.get_json(silent=True) or {}
        database_name = data.get("database_name")
        if not database_name:
            return jsonify({"error": "Missing database_name"}), 400
        chroma_path, collection_name = _parse_common_payload(data)
        collection = _get_collection(chroma_path, collection_name)
        results = collection.get(
            where={"database_name": database_name},
            include=["documents", "metadatas"],
        )
        items = []
        for doc_id, doc, meta in zip(
            results.get("ids") or [],
            results.get("documents") or [],
            results.get("metadatas") or [],
        ):
            metadata = meta or {}
            items.append(
                {
                    "id": doc_id,
                    "document": (doc or "").strip(),
                    "metadata": metadata,
                    "is_original": bool(metadata.get("original", False)),
                }
            )
        return jsonify({"items": items})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("get_business_info server view_all failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/insert", methods=["POST"])
def insert():
    try:
        import uuid

        data = request.get_json(silent=True) or {}
        database_name = data.get("database_name")
        info_string = (data.get("info_string") or "").strip()
        if not database_name:
            return jsonify({"error": "Missing database_name"}), 400
        if not info_string:
            return jsonify({"error": "Missing info_string"}), 400
        chroma_path, collection_name = _parse_common_payload(data)
        collection = _get_collection(chroma_path, collection_name)

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"inserted:{info_string}"))
        existing = collection.get(ids=[doc_id])
        if existing and existing.get("ids"):
            return jsonify({"status": "exists", "id": doc_id, "content": info_string})

        collection.add(
            ids=[doc_id],
            documents=[info_string],
            metadatas=[
                {
                    "database_name": database_name,
                    "original": False,
                }
            ],
        )
        return jsonify({"status": "inserted", "id": doc_id, "content": info_string})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("get_business_info server insert failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/delete", methods=["POST"])
def delete():
    try:
        data = request.get_json(silent=True) or {}
        document_id = data.get("document_id")
        if not document_id:
            return jsonify({"error": "Missing document_id"}), 400
        chroma_path, collection_name = _parse_common_payload(data)
        collection = _get_collection(chroma_path, collection_name)

        existing = collection.get(ids=[document_id])
        if not existing or not existing.get("ids"):
            return jsonify({"error": f"Document with ID '{document_id}' not found"}), 404

        metadata = (existing.get("metadatas") or [{}])[0] or {}
        if metadata.get("original", False):
            return (
                jsonify(
                    {
                        "error": (
                            f"Cannot delete original/pre-existing business info (ID: {document_id})"
                        )
                    }
                ),
                400,
            )

        deleted_doc = ((existing.get("documents") or ["(unknown)"])[0]) or "(unknown)"
        collection.delete(ids=[document_id])
        return jsonify({"status": "deleted", "id": document_id, "content": deleted_doc})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("get_business_info server delete failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.get_json(silent=True) or {}
        chroma_path, collection_name = _parse_common_payload(data)
        submission_output_path = data.get("submission_output_path")

        collection = _get_collection(chroma_path, collection_name)
        results = collection.get(include=["documents", "metadatas"])
        ids = results.get("ids") or []
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []

        total_count = len(ids)
        original_count = sum(1 for meta in metadatas if (meta or {}).get("original", False))
        inserted_count = total_count - original_count
        submission_data = {
            "total_strings": total_count,
            "original_strings": original_count,
            "inserted_strings": inserted_count,
            "documents": [],
        }
        for doc_id, doc, meta in zip(ids, documents, metadatas):
            metadata = meta or {}
            submission_data["documents"].append(
                {
                    "id": doc_id,
                    "content": doc,
                    "is_original": bool(metadata.get("original", False)),
                    "database_name": metadata.get("database_name", "unknown"),
                }
            )

        if submission_output_path:
            output_path = Path(submission_output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(submission_data, f, indent=2)

        return jsonify(
            {
                "summary": {
                    "total_strings": total_count,
                    "original_strings": original_count,
                    "inserted_strings": inserted_count,
                },
                "submission_data": submission_data,
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("get_business_info server submit failed")
        return jsonify({"error": str(exc)}), 500


def main():
    parser = argparse.ArgumentParser(description="Business info query server")
    parser.add_argument("--port", type=int, default=9531, help="Port to run on")
    parser.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip model warmup at startup",
    )
    args = parser.parse_args()

    if not args.skip_warmup:
        _warm_embedding_model()

    logger.info("Starting get_business_info server on port %s", args.port)
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
