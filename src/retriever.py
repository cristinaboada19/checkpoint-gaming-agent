import json
import os
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings


ROOT_DIR = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"

INDEX_PATH = VECTOR_STORE_DIR / "checkpoint.index"
CHUNKS_PATH = VECTOR_STORE_DIR / "chunks.json"


def load_vector_store():
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el índice vectorial: {INDEX_PATH}"
        )

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de chunks: {CHUNKS_PATH}"
        )

    index = faiss.read_index(str(INDEX_PATH))

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    return index, chunks


def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    load_dotenv(ROOT_DIR / ".env")

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "No se encontró GOOGLE_API_KEY en el archivo .env"
        )

    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        output_dimensionality=768,
    )


def retrieve_documents(
    query: str,
    top_k: int = 4,
    score_threshold: float = 0.35,
    category: str | None = None,
) -> list[dict[str, Any]]:
    if not query.strip():
        return []

    index, chunks = load_vector_store()
    embeddings_model = get_embeddings_model()

    query_vector = embeddings_model.embed_query(query)

    query_array = np.asarray(
        [query_vector],
        dtype=np.float32,
    )

    faiss.normalize_L2(query_array)

    fetch_k = min(
        max(top_k * 3, 10),
        index.ntotal,
    )

    scores, indices = index.search(
        query_array,
        fetch_k,
    )

    results = []

    for score, chunk_index in zip(scores[0], indices[0]):
        if chunk_index == -1:
            continue

        if float(score) < score_threshold:
            continue

        chunk = chunks[chunk_index]
        metadata = chunk.get("metadata", {})

        if category:
            chunk_category = metadata.get("category", "")

            if chunk_category.lower() != category.lower():
                continue

        results.append(
            {
                "page_content": chunk["page_content"],
                "metadata": metadata,
                "score": float(score),
            }
        )

        if len(results) >= top_k:
            break

    return results


def build_context(
    results: list[dict[str, Any]],
) -> str:
    if not results:
        return ""

    context_parts = []

    for number, result in enumerate(results, start=1):
        metadata = result["metadata"]

        source = metadata.get(
            "source",
            "Fuente desconocida",
        )

        page = metadata.get(
            "page",
            "N/D",
        )

        category = metadata.get(
            "category",
            "Sin categoría",
        )

        content = result["page_content"]

        context_part = (
            f"[FUENTE {number}]\n"
            f"Documento: {source}\n"
            f"Página: {page}\n"
            f"Categoría: {category}\n"
            f"Contenido:\n{content}"
        )

        context_parts.append(context_part)

    return "\n\n---\n\n".join(context_parts)


if __name__ == "__main__":
    question = "Mi pedido figura entregado pero nunca lo recibí, ¿qué tengo que hacer?"

    print(f"\nPregunta: {question}")

    results = retrieve_documents(question)

    print(f"Fragmentos recuperados: {len(results)}")

    for number, result in enumerate(results, start=1):
        print(f"\n--- RESULTADO {number} ---")

        print(f"Score: {result['score']:.4f}")

        print(
            f"Fuente: "
            f"{result['metadata'].get('source')}"
        )

        print(
            f"Página: "
            f"{result['metadata'].get('page')}"
        )

        print(result["page_content"][:500])

    context = build_context(results)

    print("\n\n--- CONTEXTO ENSAMBLADO ---\n")

    print(context[:3000])