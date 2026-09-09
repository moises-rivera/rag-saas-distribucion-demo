"""Punto de entrada del RAG final, ejecutable con ``python -m rag_final.main``."""

from .service import answer_question, initialize_service


def _show_result(result):
    print("\nRESPUESTA DEL RAG")
    print("=" * 70)
    print(result["answer"])
    print(f"\nModo: {result['mode']}")
    print("\nFUENTES RECUPERADAS")
    print("=" * 70)
    for source in result["sources"]:
        print(
            f"{source['rank']}. {source['source']} | "
            f"chunk {source['chunk_id']} | "
            f"estructura: {source['structure']} | "
            f"RRF: {source['rrf_score']:.6f} | "
            f"Reranker score: {source['reranker_score']:.6f}"
        )


def main():
    try:
        chunk_count = initialize_service()
    except RuntimeError as error:
        print(f"No se puede construir el índice: {error}")
        return

    print("ÍNDICE LISTO")
    print(f"Chunks indexados: {chunk_count}")
    print("Escribe 'salir' para terminar.")

    while True:
        try:
            question = input("\nPregunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesión finalizada.")
            break

        if question.lower() == "salir":
            print("Sesión finalizada.")
            break
        if not question:
            continue

        try:
            _show_result(answer_question(question))
        except RuntimeError as error:
            print(f"No se pudo generar la respuesta: {error}")


if __name__ == "__main__":
    main()
