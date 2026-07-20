from pathlib import Path
import re

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Ruta a la carpeta que contiene los documentos
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# Información adicional de cada documento
DOCUMENT_METADATA = {
    "01_manual_atencion_postventa.pdf": {
        "category": "Atención al cliente y postventa",
        "responsible_area": "Customer Experience / Soporte Técnico",
    },
    "02_politica_compras_pagos_envios.pdf": {
        "category": "Compras, pagos y logística",
        "responsible_area": "E-commerce / Finanzas / Logística",
    },
    "03_faq_colaboradores.pdf": {
        "category": "Base de conocimiento / FAQ",
        "responsible_area": "Customer Experience",
    },
}


def clean_text(text: str) -> str:
    """
    Limpia problemas básicos de extracción sin modificar
    el significado del contenido.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def load_pdf(pdf_path: Path) -> list[Document]:
    """
    Extrae el contenido de un PDF página por página
    y lo convierte en documentos de LangChain.
    """
    reader = PdfReader(pdf_path)

    metadata_info = DOCUMENT_METADATA.get(pdf_path.name, {})

    documents = []

    for page_number, page in enumerate(reader.pages, start=1):

        extracted_text = page.extract_text() or ""

        clean_content = clean_text(extracted_text)

        if not clean_content:
            continue

        document = Document(
            page_content=clean_content,
            metadata={
                "source": pdf_path.name,
                "page": page_number,
                "category": metadata_info.get(
                    "category",
                    "Sin categoría"
                ),
                "responsible_area": metadata_info.get(
                    "responsible_area",
                    "No especificada"
                ),
            },
        )

        documents.append(document)

    return documents


def load_all_documents() -> list[Document]:
    """
    Busca y procesa todos los archivos PDF
    presentes en la carpeta data.
    """
    documents = []

    for pdf_path in sorted(DATA_DIR.glob("*.pdf")):
        documents.extend(load_pdf(pdf_path))

    return documents


def split_documents(
    documents: list[Document],
) -> list[Document]:
    """
    Divide los documentos en fragmentos más pequeños
    conservando sus metadatos.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return text_splitter.split_documents(documents)


if __name__ == "__main__":

    documents = load_all_documents()

    chunks = split_documents(documents)

    print(f"Páginas procesadas: {len(documents)}")
    print(f"Chunks generados: {len(chunks)}")

    if chunks:
        print("\n--- EJEMPLO DE CHUNK ---")

        print(chunks[0].page_content[:500])

        print("\n--- METADATOS ---")

        print(chunks[0].metadata)
        