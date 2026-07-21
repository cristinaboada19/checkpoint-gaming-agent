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


def format_history(
    history: list[dict[str, Any]] | None,
) -> str:
    if not history:
        return "Sin historial previo."

    lines = []

    for message in history[-6:]:
        role = (
            "Colaborador"
            if message["role"] == "user"
            else "Agente"
        )

        lines.append(
            f"{role}: {message['content']}"
        )

    return "\n".join(lines)

def build_search_query(
    question: str,
    history: list[dict[str, Any]] | None,
) -> str:
    if not history:
        return question

    normalized = question.strip().lower()

    follow_up_starts = (
        "¿y ",
        "y ",
        "¿y si",
        "y si",
        "entonces",
        "¿entonces",
        "en ese caso",
        "¿en ese caso",
    )

    follow_up_terms = (
        "eso",
        "ese caso",
        "esa situación",
        "lo mismo",
    )

    is_follow_up = (
        normalized.startswith(follow_up_starts)
        or any(
            term in normalized
            for term in follow_up_terms
        )
    )

    if not is_follow_up:
        return question

    previous_questions = [
        message["content"]
        for message in history
        if message["role"] == "user"
    ]

    if not previous_questions:
        return question

    return (
        f"Contexto de la consulta anterior: "
        f"{previous_questions[-1]}\n"
        f"Pregunta actual: {question}"
    )

def generate_answer(
    question: str,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    search_query = build_search_query(
        question,
        history,
    )

    results = retrieve_documents(search_query)

    if not results:
        return {
            "answer": (
                "No encontré esta información en los "
                "documentos disponibles de Checkpoint Gaming."
            ),
            "sources": [],
        }

    context = build_context(results)
    history_text = format_history(history)

    system_prompt = """
Eres el asistente interno de inteligencia artificial de Checkpoint Gaming.

Tu función es responder consultas de colaboradores utilizando únicamente
la información contenida en el contexto documental proporcionado.

Reglas:
- Responde únicamente con información respaldada por el contexto documental.
- No utilices conocimiento externo.
- No inventes políticas, procedimientos, plazos, condiciones ni datos.
- Si el contexto no contiene información suficiente para responder,
  indica claramente que no encontraste esa información en los documentos disponibles.
- El historial sirve únicamente para comprender la continuidad de la conversación.
- El historial no debe utilizarse como fuente factual.
- Responde de forma clara, directa y profesional.
- No inventes nombres de documentos ni números de página.
"""

    human_prompt = f"""
HISTORIAL DE CONVERSACIÓN:

{history_text}

CONTEXTO DOCUMENTAL:

{context}

PREGUNTA ACTUAL DEL COLABORADOR:

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

    return {
        "answer": response.content,
        "sources": get_sources(results),
    }


if __name__ == "__main__":
    question = "¿Qué pasa si un producto llega dañado?"

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