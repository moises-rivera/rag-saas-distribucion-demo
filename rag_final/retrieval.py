"""Índice híbrido: embeddings, BM25 y Reciprocal Rank Fusion."""

import re
import unicodedata

import numpy as np


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RRF_K = 60
TOP_K = 5
CANDIDATE_DEPTH = 50
RERANK_CANDIDATES = 50
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def tokenize(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.findall(r"\b\w+\b", normalized, flags=re.UNICODE)


def _normalize_rows(values):
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-12)


class RetrievalIndex:
    """Índice en memoria para un corpus pequeño o mediano de Markdown."""

    def __init__(self, chunks, model_name=MODEL_NAME):
        if not chunks:
            raise ValueError("El corpus no contiene chunks.")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Falta sentence-transformers; instálalo manualmente antes de ejecutar."
            ) from error
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as error:
            raise RuntimeError(
                "Falta rank_bm25; no se instalará automáticamente. "
                "Instálalo manualmente para habilitar la búsqueda BM25."
            ) from error
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as error:
            raise RuntimeError(
                "Falta CrossEncoder de sentence-transformers; "
                "instala sentence-transformers manualmente."
            ) from error

        self.chunks = chunks
        self.model = SentenceTransformer(model_name, device="cpu")
        try:
            self.reranker = CrossEncoder(RERANKER_MODEL_NAME, device="cpu")
        except Exception as error:
            raise RuntimeError(
                f"No se pudo cargar el reranker local '{RERANKER_MODEL_NAME}'."
            ) from error
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        self.embeddings = _normalize_rows(embeddings)
        self.bm25 = BM25Okapi([tokenize(text) for text in texts])

    def search(self, question, top_k=TOP_K):
        """Devuelve resultados ordenados por RRF, con posiciones 1-based."""
        question_embedding = self.model.encode(
            [question], convert_to_numpy=True, show_progress_bar=False
        )
        question_embedding = _normalize_rows(question_embedding)[0]
        semantic_scores = self.embeddings @ question_embedding
        bm25_scores = np.asarray(self.bm25.get_scores(tokenize(question)))

        semantic_order = np.argsort(-semantic_scores, kind="stable")[:CANDIDATE_DEPTH]
        semantic_rank = {index: rank for rank, index in enumerate(semantic_order, 1)}

        bm25_order = np.argsort(-bm25_scores, kind="stable")
        # Los scores BM25 cero no son señal léxica y no deben crear rankings
        # arbitrarios para RRF según la posición del chunk en el corpus.
        bm25_candidates = [
            index for index in bm25_order if bm25_scores[index] > 0
        ][:CANDIDATE_DEPTH]
        bm25_rank = {index: rank for rank, index in enumerate(bm25_candidates, 1)}

        candidate_indexes = set(semantic_rank) | set(bm25_rank)
        rrf_scores = {
            index: (
                (1 / (RRF_K + semantic_rank[index]) if index in semantic_rank else 0)
                + (1 / (RRF_K + bm25_rank[index]) if index in bm25_rank else 0)
            )
            for index in candidate_indexes
        }
        rrf_candidates = sorted(
            rrf_scores, key=lambda index: (-rrf_scores[index], index)
        )[:RERANK_CANDIDATES]
        reranker_pairs = [
            (
                question,
                "Fuente: "
                f"{self.chunks[index]['source']}\n"
                "Estructura: "
                f"{self.chunks[index]['estructura']}\n"
                "Contenido:\n"
                f"{self.chunks[index]['text']}",
            )
            for index in rrf_candidates
        ]
        reranker_scores = self.reranker.predict(reranker_pairs)
        reranked_indexes = sorted(
            zip(rrf_candidates, reranker_scores),
            key=lambda item: (-float(item[1]), item[0]),
        )[:top_k]

        return [
            {
                **self.chunks[index],
                "semantic_rank": semantic_rank.get(index),
                "bm25_rank": bm25_rank.get(index),
                "rrf_score": rrf_scores[index],
                "reranker_score": float(reranker_score),
            }
            for index, reranker_score in reranked_indexes
        ]
