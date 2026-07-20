import json
import os
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from document_loader import load_all_documents, split_documents


# Rutas principales del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"

INDEX_PATH = VECTOR_STORE_DIR / "checkpoint.index"
CHUNKS_PATH = VECTOR_STORE_DIR / "chunks.json"


def create_vector_index() -> None:
    """
    Procesa los documentos, genera embeddings con Gemini
    y crea un índice vectorial local con FAISS.
    """

    
    load_dotenv(ROOT_DIR / ".env")

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "No se encontró GOOGLE_API_KEY en el archivo .env"
        )

    
    VECTOR_STORE_DIR.mkdir(exist_ok=True)

    documents = load_all_documents()
    chunks = split_documents(documents)

    if not chunks:
        raise RuntimeError(
            "No se encontraron chunks para indexar."
        )

    print(f"Chunks a indexar: {len(chunks)}")

    # Modelo de embeddings
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        output_dimensionality=768,
    )

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    print("Generando embeddings...")

    vectors = embeddings_model.embed_documents(texts)

    # Convertir a matriz NumPy compatible con FAISS
    vectors_array = np.asarray(
        vectors,
        dtype=np.float32,
    )

    faiss.normalize_L2(vectors_array)

    dimension = vectors_array.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(vectors_array)

    faiss.write_index(
        index,
        str(INDEX_PATH),
    )

    chunks_data = []

    for chunk in chunks:
        chunks_data.append(
            {
                "page_content": chunk.page_content,
                "metadata": chunk.metadata,
            }
        )

    with open(
        CHUNKS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            chunks_data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n--- INDEXACIÓN COMPLETADA ---")
    print(f"Vectores almacenados: {index.ntotal}")
    print(f"Dimensiones por vector: {dimension}")

    print(
        f"Índice guardado en: "
        f"{INDEX_PATH.relative_to(ROOT_DIR)}"
    )

    print(
        f"Chunks guardados en: "
        f"{CHUNKS_PATH.relative_to(ROOT_DIR)}"
    )


if __name__ == "__main__":
    create_vector_index()