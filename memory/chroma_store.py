"""ChromaDB vector store — seed from JSON and RAG retrieval."""
from __future__ import annotations
import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

_COLLECTION = "cyclone_history"
_EMBED_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_DB   = Path(__file__).parent.parent / "chroma_db"


class ChromaStore:
    def __init__(self, db_path: str | Path = _DEFAULT_DB):
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._ef = SentenceTransformerEmbeddingFunction(model_name=_EMBED_MODEL)
        self._col = self._client.get_or_create_collection(
            name=_COLLECTION,
            embedding_function=self._ef,
        )

    # ------------------------------------------------------------------
    def seed(self, json_path: str | Path | None = None) -> None:
        """Load cyclone records from JSON into ChromaDB (idempotent)."""
        if json_path is None:
            json_path = Path(__file__).parent.parent / "data" / "seed_cyclones.json"
        records: list[dict] = json.loads(Path(json_path).read_text())

        existing_ids = set(self._col.get(include=[])["ids"])
        new = [r for r in records if r["id"] not in existing_ids]
        if not new:
            return

        self._col.add(
            ids=[r["id"] for r in new],
            documents=[r["summary"] for r in new],
            metadatas=[{k: v for k, v in r.items() if k != "summary"} for r in new],
        )

    # ------------------------------------------------------------------
    def retrieve(self, query: str, k: int = 2) -> list[dict]:
        """Return top-k relevant documents as list of {id, summary, metadata}."""
        results = self._col.query(query_texts=[query], n_results=min(k, self._col.count()))
        docs = []
        for i, doc_id in enumerate(results["ids"][0]):
            docs.append({
                "id":       doc_id,
                "summary":  results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            })
        return docs
