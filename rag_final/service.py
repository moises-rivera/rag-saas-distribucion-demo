"""Servicio compartido por la consola y la interfaz web del RAG."""

import re
from pathlib import Path
from threading import Lock
import unicodedata

from dotenv import load_dotenv

from .chunking import load_chunks
from .generation import generate_grounded_answer
from .retrieval import RetrievalIndex
from .structured import deterministic_answer, parse_permission_table


PERMISSION_TERMS = {
    "permiso", "permisos", "rol", "roles", "autorizado", "autorizados",
    "autorizacion",
}
KNOWN_ROLES = {
    "dueno", "admin", "administrador", "contador", "vendedor", "cajero",
    "almacen", "almacenero", "cobrador", "consulta",
}
QUESTION_WORDS = {
    "quien", "quienes", "puede", "pueden", "el", "la", "los", "las",
    "un", "una", "de", "del", "para", "por", "que",
}
ARTICLES = {"el", "la", "los", "las"}

_initialization_lock = Lock()
_index = None
_chunk_count = 0


def _load_local_environment():
    """Carga la configuración local antes de resolver el directorio del corpus."""
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=project_root / ".env")


def _normalized_tokens(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.findall(r"\b\w+\b", normalized)


def _normalized_words(text):
    return set(_normalized_tokens(text))


def is_permission_question(question):
    """Detecta de forma determinista intención de permisos o roles."""
    tokens = _normalized_tokens(question)
    words = set(tokens)
    has_permission_term = bool(PERMISSION_TERMS & words)
    has_who_and_can = bool({"quien", "quienes"} & words) and bool(
        {"puede", "pueden"} & words
    )
    if has_permission_term or has_who_and_can:
        return True

    can_indexes = [
        index for index, token in enumerate(tokens) if token in {"puede", "pueden"}
    ]
    if not can_indexes:
        return False
    if tokens[0] in {"puede", "pueden"}:
        return True

    first_content_index = 0
    while first_content_index < len(tokens) and tokens[first_content_index] in ARTICLES:
        first_content_index += 1
    return (
        first_content_index < len(tokens)
        and tokens[first_content_index] in KNOWN_ROLES
        and any(index > first_content_index for index in can_indexes)
    )


def permission_action_matches_question(question, facts):
    """Comprueba que la acción de permisos corresponda con la pregunta."""
    question_words = _normalized_words(question) - QUESTION_WORDS
    action_words = _normalized_words(facts["action"]) - QUESTION_WORDS
    return bool(action_words) and action_words <= question_words


def initialize_service():
    """Carga el corpus y construye el índice una sola vez por proceso."""
    global _index, _chunk_count

    if _index is not None:
        return _chunk_count

    with _initialization_lock:
        if _index is None:
            _load_local_environment()
            chunks = load_chunks()
            if not chunks:
                raise RuntimeError(
                    "No se encontraron archivos Markdown en el corpus configurado."
                )
            _index = RetrievalIndex(chunks)
            _chunk_count = len(chunks)
    return _chunk_count


def _public_sources(results):
    return [
        {
            "rank": rank,
            "source": result["source"],
            "chunk_id": result["chunk_id"],
            "structure": result["estructura"],
            "rrf_score": float(result["rrf_score"]),
            "reranker_score": float(result["reranker_score"]),
        }
        for rank, result in enumerate(results, 1)
    ]


def answer_question(question):
    """Responde una pregunta y devuelve respuesta, modo y fuentes ordenadas."""
    if not isinstance(question, str):
        raise ValueError("La pregunta debe ser texto.")

    question = question.strip()
    if not question:
        raise ValueError("La pregunta no puede estar vacía.")

    initialize_service()
    results = _index.search(question, top_k=5)

    if is_permission_question(question):
        for result in results:
            facts = parse_permission_table(result["text"])
            if facts is not None and permission_action_matches_question(question, facts):
                return {
                    "answer": deterministic_answer(facts),
                    "mode": "structured",
                    "sources": _public_sources(results),
                }

    return {
        "answer": generate_grounded_answer(question, results),
        "mode": "narrative",
        "sources": _public_sources(results),
    }
