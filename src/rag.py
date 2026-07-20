import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from retriever import build_context, retrieve_documents


ROOT_DIR = Path(__file__).resolve().parent.parent


def get_llm() -> ChatGoogleGenerativeAI:
    load_dotenv(ROOT_DIR / ".env")

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "No se encontró GOOGLE_API_KEY en el archivo .env"
        )

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
    )


def get_sources(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sources = []
    seen = set()

    for result in results:
        metadata = result["metadata"]

        source = metadata.get(
            "source",
            "Fuente desconocida",
        )

        page = metadata.get(
            "page",
            "N/D",
        )

        key = (source, page)

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "source": source,
                "page": page,
                "category": metadata.get(
                    "category",
                    "Sin categoría",
                ),
            }
        )

    return sources


def generate_answer(
    question: str,
) -> dict[str, Any]:
    results = retrieve_documents(question)

    if not results:
        return {
            "answer": (
                "No encontré esta información en los "
                "documentos disponibles de Checkpoint Gaming."
            ),
            "sources": [],
        }

    context = build_context(results)

    system_prompt = """
Eres el asistente interno de Checkpoint Gaming.

Tu función es responder consultas de colaboradores utilizando únicamente
la información contenida en el contexto documental proporcionado.

Reglas:
- Responde únicamente con información respaldada por el contexto.
- No utilices conocimiento externo.
- No inventes políticas, procedimientos, plazos, condiciones ni datos.
- Si el contexto no contiene información suficiente para responder,
  indica claramente que no encontraste esa información en los documentos disponibles.
- Responde de forma clara, directa y profesional.
- No inventes nombres de documentos ni números de página.
"""

    human_prompt = f"""
CONTEXTO DOCUMENTAL:

{context}

PREGUNTA DEL COLABORADOR:

{question}

Responde únicamente basándote en el contexto documental.
"""

    llm = get_llm()

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )

    answer = response.content

    return {
        "answer": answer,
        "sources": get_sources(results),
    }


if __name__ == "__main__":
    question = "El cliente dice que su pedido figura como entregado pero no lo recibió, cómo procedemos?"

    result = generate_answer(question)

    print(f"\nPregunta: {question}")
    print(f"\nRespuesta:\n{result['answer']}")

    print("\nFuentes:")

    if result["sources"]:
        for source in result["sources"]:
            print(
                f"- {source['source']} "
                f"| Página {source['page']} "
                f"| {source['category']}"
            )
    else:
        print("- Sin fuentes")