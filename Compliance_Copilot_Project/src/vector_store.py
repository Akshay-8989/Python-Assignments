"""
vector_store.py
---------------
FR3 – Embedding Generation : TF-IDF sparse → dense numpy vectors (local, offline)
FR4 – Vector Database Storage: FAISS index persisted to disk
FR6 – Context Retrieval    : FAISS similarity search

Why TF-IDF → FAISS instead of neural embeddings?
  - Zero internet / zero downloads needed
  - scikit-learn + faiss-cpu are pure pip installs
  - TF-IDF gives float32 dense vectors that FAISS indexes natively
  - SVD truncation keeps vector dimension manageable (256-d)
  - For policy documents with specific terminology this works very well
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

FAISS_INDEX_FILE = "faiss_index.bin"
META_FILE        = "faiss_meta.pkl"
TFIDF_FILE       = "tfidf_vectorizer.pkl"
SVD_FILE         = "svd_transformer.pkl"

VECTOR_DIM = 256      # SVD output dimension — compact but expressive


class _Doc:
    """Minimal document object."""
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata     = metadata


def _expand_query(query: str) -> str:
    """Expand query with banking synonyms for better TF-IDF recall."""
    q   = query.lower()
    exp = [query]

    mapping = {
        ("kyc", "know your customer", "identity", "identification", "verify", "id proof"):
            "kyc know your customer identity verification document proof",
        ("aml", "money laundering", "anti-money", "laundering"):
            "aml anti money laundering suspicious activity",
        ("sar", "suspicious activity", "report", "filing"):
            "sar suspicious activity report filing mlro",
        ("risk", "assessment", "cdd", "edd", "due diligence"):
            "risk assessment customer due diligence cdd edd enhanced",
        ("document", "proof", "certificate", "passport", "licence", "id"):
            "documents required proof identity address passport licence",
        ("threshold", "limit", "amount", "usd", "cash", "transaction"):
            "threshold limit reporting amount cash transaction usd 10000",
        ("penalty", "fine", "punishment", "consequence", "violation", "enforcement"):
            "penalty fine enforcement consequences non-compliance violation",
        ("record", "retain", "keep", "store", "how long", "retention"):
            "record keeping retention period years store documents",
        ("train", "employee", "staff", "mandatory", "annual"):
            "training employees staff mandatory annual compliance",
        ("sanction", "ofac", "blacklist", "watchlist", "screen"):
            "sanctions screening ofac watchlist blacklist",
        ("pep", "politically exposed", "politician"):
            "pep politically exposed person enhanced due diligence",
        ("fail", "reject", "denied", "not pass", "unsuccessful"):
            "customer fails kyc check rejected denied account closure",
        ("escalat", "approval", "senior", "management"):
            "escalation approval senior management compliance officer",
        ("image", "chart", "table", "diagram", "figure"):
            "image chart table diagram figure visual",
    }
    for keywords, expansion in mapping.items():
        if any(w in q for w in keywords):
            exp.append(expansion)

    return " ".join(exp)


class ComplianceVectorStore:
    """
    FAISS-backed vector store using TF-IDF + SVD embeddings.
    Fully offline — no HuggingFace, no internet.
    """

    def __init__(self, persist_dir: Path, embedding_model: str = None):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self._index      = None   # faiss.IndexFlatIP
        self._texts:  List[str]  = []
        self._metas:  List[dict] = []
        self._vectorizer = None   # TfidfVectorizer
        self._svd        = None   # TruncatedSVD

        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        faiss_path = self.persist_dir / FAISS_INDEX_FILE
        meta_path  = self.persist_dir / META_FILE
        tfidf_path = self.persist_dir / TFIDF_FILE
        svd_path   = self.persist_dir / SVD_FILE

        if all(p.exists() for p in [faiss_path, meta_path, tfidf_path, svd_path]):
            try:
                import faiss
                self._index = faiss.read_index(str(faiss_path))
                with open(meta_path,  "rb") as f:
                    data = pickle.load(f)
                    self._texts = data["texts"]
                    self._metas = data["metas"]
                with open(tfidf_path, "rb") as f:
                    self._vectorizer = pickle.load(f)
                with open(svd_path,   "rb") as f:
                    self._svd = pickle.load(f)
                logger.info("FAISS index loaded: %d vectors", self._index.ntotal)
            except Exception as e:
                logger.warning("Could not load FAISS index: %s — rebuilding.", e)
                self._reset_state()

    def _save(self):
        import faiss
        faiss.write_index(self._index, str(self.persist_dir / FAISS_INDEX_FILE))
        with open(self.persist_dir / META_FILE,  "wb") as f:
            pickle.dump({"texts": self._texts, "metas": self._metas}, f)
        with open(self.persist_dir / TFIDF_FILE, "wb") as f:
            pickle.dump(self._vectorizer, f)
        with open(self.persist_dir / SVD_FILE,   "wb") as f:
            pickle.dump(self._svd, f)
        logger.info("FAISS index saved: %d vectors", self._index.ntotal)

    def _reset_state(self):
        self._index      = None
        self._texts      = []
        self._metas      = []
        self._vectorizer = None
        self._svd        = None

    # ── Embedding ─────────────────────────────────────────────────────────────

    def _embed(self, texts: List[str]) -> np.ndarray:
        """
        Convert texts → float32 dense vectors using TF-IDF + SVD.
        Vectors are L2-normalised for cosine similarity via inner product.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.preprocessing import normalize

        # Fit on all texts
        self._vectorizer = TfidfVectorizer(
            max_features=16384,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            strip_accents="unicode",
        )
        sparse = self._vectorizer.fit_transform(texts)   # (n, vocab)

        # Reduce to VECTOR_DIM with SVD (like LSA)
        actual_dim = min(VECTOR_DIM, sparse.shape[1] - 1, sparse.shape[0] - 1)
        self._svd  = TruncatedSVD(n_components=actual_dim, random_state=42)
        dense      = self._svd.fit_transform(sparse)      # (n, actual_dim)

        # L2 normalise → cosine sim = inner product
        dense = normalize(dense, norm="l2").astype(np.float32)
        return dense

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed a single query using the fitted vectorizer + SVD."""
        from sklearn.preprocessing import normalize
        sparse = self._vectorizer.transform([query])
        dense  = self._svd.transform(sparse)
        dense  = normalize(dense, norm="l2").astype(np.float32)
        return dense   # shape (1, dim)

    # ── Public API ────────────────────────────────────────────────────────────

    def add_documents(self, chunks) -> None:
        if not chunks:
            return

        import faiss

        new_texts = [c.text for c in chunks]
        new_metas = [
            {
                "source":      c.source_file,
                "page":        c.page_number,
                "chunk_index": c.chunk_index,
                "doc_hash":    c.doc_hash,
                "chunk_type":  getattr(c, "chunk_type", "text"),
            }
            for c in chunks
        ]

        all_texts = self._texts + new_texts
        all_metas = self._metas + new_metas

        logger.info("Building TF-IDF + SVD embeddings for %d chunks…", len(all_texts))
        vectors = self._embed(all_texts)   # (n, dim)

        dim = vectors.shape[1]
        # IndexFlatIP = exact inner product search (cosine sim after L2 norm)
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(vectors)

        self._texts = all_texts
        self._metas = all_metas

        self._save()
        logger.info("FAISS index built: %d vectors, dim=%d", self._index.ntotal, dim)

    def similarity_search(self, query: str, k: int = 4) -> List[Tuple[_Doc, float]]:
        if self._index is None or self._index.ntotal == 0:
            raise RuntimeError("Vector store is empty. Upload a PDF first.")

        expanded  = _expand_query(query)
        query_vec = self._embed_query(expanded)   # (1, dim)

        k_actual  = min(k, self._index.ntotal)
        scores, indices = self._index.search(query_vec, k_actual)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((_Doc(
                page_content=self._texts[idx],
                metadata=self._metas[idx],
            ), float(score)))

        # Always return something
        if not results:
            results = [(_Doc(
                page_content=self._texts[0],
                metadata=self._metas[0],
            ), 0.01)]

        return results

    def document_count(self) -> int:
        return self._index.ntotal if self._index else 0

    def reset(self):
        import shutil
        for f in [FAISS_INDEX_FILE, META_FILE, TFIDF_FILE, SVD_FILE]:
            p = self.persist_dir / f
            if p.exists():
                p.unlink()
        self._reset_state()
        logger.info("FAISS vector store reset.")
