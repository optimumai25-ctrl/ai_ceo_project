import pickle
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
import faiss
import openai


EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
INDEX_PATH = Path("embeddings/faiss.index")
META_PATH = Path("embeddings/metadata.pkl")


def embed_query(text: str) -> np.ndarray:
    response = openai.Embedding.create(model=EMBED_MODEL, input=text)
    vec = response["data"][0]["embedding"]
    arr = np.array(vec, dtype=np.float32)
    return arr


def load_resources():
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def search(query: str, k: int = 5) -> List[Tuple[int, float, Dict]]:
    index, metadata = load_resources()
    qvec = embed_query(query).reshape(1, -1)
    D, I = index.search(qvec, k)
    return [(int(i), float(d), metadata.get(int(i), {})) for d, i in zip(D[0], I[0]) if i != -1]
