import streamlit as st

from config.settings import settings
from src.prompts.loader import PromptLoader
from src.rag.index_manager import IndexManager
from src.services.chat_service import ChatService
from src.services.session_service import SessionService
from src.storage.session_repository import SessionRepository


st.set_page_config(page_title="Tutor Maturalny CKE", page_icon="📐", layout="centered")

prompt_loader = PromptLoader(settings.storage_dir.parent / "config" / "prompts")

st.sidebar.header("Ustawienia")
session_repository = SessionRepository(settings.storage_dir / "sessions.sqlite3")
session_service = SessionService(session_repository)
current_conversation_id = session_service.ensure_current(
    st.session_state.get("conversation_id")
)

if st.sidebar.button("Nowa rozmowa"):
    current_conversation_id = session_service.create_new()
    st.session_state.conversation_id = current_conversation_id
    st.session_state.pop("messages", None)
    st.rerun()

conversation_options = session_service.list_conversations()
selected_conversation_id = st.sidebar.selectbox(
    "Historia rozmów:",
    [conversation_id for conversation_id, _ in conversation_options],
    index=next(
        (index for index, (conversation_id, _) in enumerate(conversation_options) if conversation_id == current_conversation_id),
        0,
    ),
    format_func=lambda conversation_id: next(
        title for item_id, title in conversation_options if item_id == conversation_id
    ),
)
if selected_conversation_id != st.session_state.get("conversation_id"):
    st.session_state.conversation_id = selected_conversation_id
    st.session_state.messages = session_service.load_messages(selected_conversation_id)

embedding_label = st.sidebar.radio(
    "Silnik wektoryzacji:",
    ["Lokalny", "OpenAI"],
    help="Lokalny model nie wymaga opłat za embeddingi, ale może działać wolniej przy pierwszym uruchomieniu.",
)
embedding_mode = "openai" if embedding_label == "OpenAI" else "local"
role_options = prompt_loader.role_choices()
role_name = st.sidebar.selectbox(
    "Rola tutora:", list(role_options), format_func=role_options.get
)
student_context = st.sidebar.text_area(
    "Kontekst ucznia (opcjonalnie):",
    placeholder="Np. poziom podstawowy, potrzebuję krótkich podpowiedzi.",
)

index_manager = IndexManager(settings, embedding_mode)
st.title("📐 Tutor CKE - Matura z Matematyki")

if not index_manager.exists() or not index_manager.is_current():
    st.warning(
        "Brak aktualnej bazy wektorowej. Zostanie utworzona na podstawie plików z katalogu data."
    )
    if st.button(f"Wygeneruj bazę ({embedding_label})"):
        with st.spinner("Tworzenie bazy wektorowej..."):
            index_manager.build()
        st.rerun()
    st.stop()


def load_index(embedding_mode: str):
    return IndexManager(settings, embedding_mode).load()


index = load_index(embedding_mode)
system_prompt = prompt_loader.build_system_prompt(role_name, student_context)

chat_configuration = (embedding_mode, role_name, student_context)
if st.session_state.get("chat_configuration") != chat_configuration:
    st.session_state.chat_service = ChatService(index, system_prompt)
    st.session_state.chat_configuration = chat_configuration

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Cześć! Baza CKE jest załadowana. O co chcesz zapytać?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Napisz pytanie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizuję CKE..."):
            answer = st.session_state.chat_service.ask(prompt)
            st.write(answer["answer"])
            if answer["sources"]:
                with st.expander("Źródła"):
                    for source in answer["sources"]:
                        page = f", strona {source['page']}" if source["page"] else ""
                        st.write(f"- {source['file']}{page}")
            session_repository.add_message(current_conversation_id, "user", prompt)
            session_repository.add_message(
                current_conversation_id,
                "assistant",
                answer["answer"],
                answer["sources"],
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": answer["answer"], "sources": answer["sources"]}
            )