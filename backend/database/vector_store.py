import os
import threading

import faiss
import httpx
import numpy as np
from huggingface_hub import set_client_factory
from sentence_transformers import SentenceTransformer

# Same SSL relaxation app.py applies process-wide (via ssl._create_unverified_context)
# for this environment's intercepted HTTPS, applied here too since huggingface_hub's
# downloader uses its own httpx client rather than the stdlib ssl default context.
set_client_factory(lambda: httpx.Client(follow_redirects=True, timeout=None, verify=False))

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size

_model = None
_indexes = {}  # namespace -> faiss index, one per embedded table (documents, answers, ...)
_lock = threading.Lock()


def _index_path(namespace):
    return os.path.join(os.path.dirname(__file__), f"faiss_{namespace}.index")


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def _get_index(namespace):
    if namespace not in _indexes:
        path = _index_path(namespace)
        if os.path.exists(path):
            _indexes[namespace] = faiss.read_index(path)
        else:
            _indexes[namespace] = faiss.IndexIDMap(faiss.IndexFlatL2(EMBEDDING_DIM))
    return _indexes[namespace]


def _save_index(namespace):
    faiss.write_index(_indexes[namespace], _index_path(namespace))


def _embed(text):
    vector = _get_model().encode([text], normalize_embeddings=True)[0]
    return np.asarray(vector, dtype="float32")


def add_embedding(namespace, item_id, text):
    """Embed `text` and store/replace its vector in FAISS under `item_id`."""
    with _lock:
        index = _get_index(namespace)
        ids = np.array([item_id], dtype="int64")
        index.remove_ids(ids)  # no-op if not already present (e.g. on create)
        index.add_with_ids(_embed(text).reshape(1, -1), ids)
        _save_index(namespace)


def remove_embedding(namespace, item_id):
    with _lock:
        index = _get_index(namespace)
        index.remove_ids(np.array([item_id], dtype="int64"))
        _save_index(namespace)


def backfill_if_needed(namespace, rows):
    """Populate the index from existing `(id, text)` rows the first time it's
    used (mirrors the seed_* once-only pattern in db.py) — skipped once the
    namespace's index file already exists on disk."""
    if os.path.exists(_index_path(namespace)):
        return
    with _lock:
        index = _get_index(namespace)
        ids, vectors = [], []
        for item_id, text in rows:
            ids.append(item_id)
            vectors.append(_embed(text))
        if ids:
            index.add_with_ids(np.array(vectors, dtype="float32"), np.array(ids, dtype="int64"))
        _save_index(namespace)


def search(namespace, query_text, k=5):
    """Return up to `k` nearest item ids for `query_text` as [{"id", "distance"}, ...]."""
    with _lock:
        index = _get_index(namespace)
        if index.ntotal == 0:
            return []
        distances, ids = index.search(_embed(query_text).reshape(1, -1), min(k, index.ntotal))
    return [
        {"id": int(item_id), "distance": float(dist)}
        for item_id, dist in zip(ids[0], distances[0])
        if item_id != -1
    ]
