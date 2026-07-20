import streamlit as st

from rag import generate_answer


st.set_page_config(
    page_title="Checkpoint Gaming AI",
    page_icon="🎮",
    layout="centered",
)


def save_feedback(index: int) -> None:
    st.session_state.messages[index]["feedback"] = (
        st.session_state[f"feedback_{index}"]
    )


if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.title("🎮 Checkpoint Gaming")

    st.caption(
        "Base de conocimiento interna"
    )

    st.info(
        "Estás conversando con un agente de inteligencia artificial. "
        "Sus respuestas se basan en la documentación interna disponible."
    )

    if st.button(
        "Nueva conversación",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


st.title("Checkpoint Gaming AI")

st.caption(
    "Consultá políticas, procedimientos y documentación interna."
)


for index, message in enumerate(
    st.session_state.messages
):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            sources = message.get(
                "sources",
                [],
            )

            if sources:
                with st.expander(
                    "Fuentes consultadas"
                ):
                    for source in sources:
                        st.markdown(
                            f"- **{source['source']}**  \n"
                            f"  Página {source['page']} · "
                            f"{source['category']}"
                        )

            feedback = message.get(
                "feedback",
                None,
            )

            st.session_state[
                f"feedback_{index}"
            ] = feedback

            st.feedback(
                "thumbs",
                key=f"feedback_{index}",
                disabled=feedback is not None,
                on_change=save_feedback,
                args=[index],
            )


if prompt := st.chat_input(
    "Escribí tu consulta..."
):
    history = list(
        st.session_state.messages
    )

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.spinner(
        "Consultando la documentación..."
    ):
        result = generate_answer(
            prompt,
            history,
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "feedback": None,
        }
    )

    st.rerun()