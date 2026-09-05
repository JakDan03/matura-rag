import streamlit as st

from config.settings import settings
from src.prompts.loader import PromptLoader
from src.rag.index_manager import IndexManager
from src.services.chat_service import ChatService
from src.services.math_service import MathService
from src.services.plot_service import PlotService
from src.services.request_router import RequestRoute, RequestRouter
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

if st.sidebar.button("Stwórz nowy chat"):
    current_conversation_id = session_service.create_new(current_conversation_id)
    st.session_state.conversation_id = current_conversation_id
    st.session_state.pop("messages", None)
    st.session_state.pop("history_selection", None)
    st.rerun()

conversation_options = session_service.list_non_empty_conversations()
conversation_ids = [conversation_id for conversation_id, _ in conversation_options]

with st.sidebar.expander("Historia chatów", expanded=True):
    if conversation_options:
        history_index = (
            conversation_ids.index(current_conversation_id)
            if current_conversation_id in conversation_ids
            else None
        )
        selected_history_id = st.selectbox(
            "Wybierz rozmowę:",
            conversation_ids,
            index=history_index,
            format_func=lambda conversation_id: next(
                title for item_id, title in conversation_options if item_id == conversation_id
            ),
            placeholder="Wybierz zapisany chat...",
            label_visibility="collapsed",
        )
        if (
            selected_history_id != st.session_state.get("conversation_id")
        ):
            st.session_state.conversation_id = selected_history_id
            st.session_state.messages = session_service.load_messages(selected_history_id)
            st.rerun()

        active_history_id = current_conversation_id
        if active_history_id in conversation_ids:
            active_title = next(
                title for item_id, title in conversation_options if item_id == active_history_id
            )
            title_key = f"chat_title_{active_history_id}"
            if st.session_state.get(title_key) != active_title:
                st.session_state[title_key] = active_title

            def save_chat_title(conversation_id=active_history_id, key=title_key):
                try:
                    session_service.rename(conversation_id, st.session_state[key])
                    st.session_state.pop("chat_title_error", None)
                except ValueError as error:
                    st.session_state.chat_title_error = str(error)

            st.text_input(
                "Nazwa chatu",
                key=title_key,
                on_change=save_chat_title,
            )
            if st.session_state.get("chat_title_error"):
                st.error(st.session_state.chat_title_error)

            if st.button("Usuń chat", key=f"delete_chat_{active_history_id}"):
                session_repository.delete_conversation(active_history_id)
                st.session_state.pop("conversation_id", None)
                st.session_state.pop("messages", None)
                st.rerun()
    else:
        st.caption("Brak zapisanych rozmów.")

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
if "student_context" not in st.session_state:
    st.session_state.student_context = ""
with st.sidebar.form("student_preferences"):
    st.text_area(
        "Kontekst ucznia (opcjonalnie):",
        value=st.session_state.student_context,
        key="student_context_draft",
        placeholder="Np. poziom podstawowy, potrzebuję krótkich podpowiedzi.",
    )
    preferences_submitted = st.form_submit_button("Zastosuj preferencje")

if preferences_submitted:
    st.session_state.student_context = st.session_state.student_context_draft
student_context = st.session_state.student_context

index_manager = IndexManager(settings, embedding_mode)
st.markdown(
    """
    <style>
    .stMarkdown h1 a { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📐 Matura z Matematyki")

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
math_service = MathService()
plot_service = PlotService(math_service)
request_router = RequestRouter()


def render_visualization(visualization: dict):
    if visualization.get("type") == "plot_2d":
        return plot_service.plot_2d(visualization["expression"])
    if visualization.get("type") == "plot_3d":
        return plot_service.plot_3d(visualization["expression"])
    if visualization.get("type") == "circle":
        return plot_service.plot_circle(
            radius=visualization.get("radius", 1.0),
            center_x=visualization.get("center_x", 0.0),
            center_y=visualization.get("center_y", 0.0),
        )
    return None


def render_message_details(message: dict):
    visualization = message.get("visualization", {})
    if visualization:
        figure = render_visualization(visualization)
        if figure is not None:
            st.plotly_chart(figure, use_container_width=True)

    retrieval_metrics = message.get("retrieval_metrics", {})
    if retrieval_metrics:
        with st.expander("Diagnostyka RAG"):
            st.json(retrieval_metrics)

    sources = message.get("sources", [])
    if sources:
        with st.expander("Źródła"):
            for source in sources:
                page = f", strona {source['page']}" if source.get("page") else ""
                score = (
                    f", podobieństwo {source['score']:.3f}"
                    if source.get("score") is not None
                    else ""
                )
                st.write(f"- {source['file']}{page}{score}")

chat_configuration = (embedding_mode, role_name, student_context)
if st.session_state.get("chat_configuration") != chat_configuration:
    st.session_state.chat_service = ChatService(
        index,
        system_prompt,
        retrieval_top_k=settings.retrieval_top_k,
        similarity_cutoff=settings.retrieval_similarity_cutoff,
    )
    st.session_state.chat_configuration = chat_configuration

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Cześć! Baza CKE jest załadowana. O co chcesz zapytać?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_message_details(message)

if prompt := st.chat_input("Napisz pytanie..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizuję CKE..."):
            routed_request = request_router.route(prompt)
            figure = None
            visualization = {}
            try:
                if routed_request.route == RequestRoute.PLOT:
                    dimensions = routed_request.plot_type or "2d"
                    expression = routed_request.payload
                    if dimensions == "circle":
                        visualization = {"type": "circle", "radius": 1.0}
                    else:
                        visualization = {
                            "type": "plot_3d" if dimensions == "3d" else "plot_2d",
                            "expression": expression,
                        }
                    figure = render_visualization(visualization)
                    answer = {
                        "answer": (
                            "Wygenerowano okrąg z oznaczonym środkiem, promieniem i średnicą."
                            if dimensions == "circle"
                            else f"Wygenerowano wykres {dimensions.upper()} dla $f = {expression}$."
                        ),
                        "sources": [],
                    }
                elif routed_request.route == RequestRoute.MATH:
                    verified_result = math_service.format_solution(routed_request.payload)
                    answer = {
                        "answer": st.session_state.chat_service.explain_math(
                            prompt, verified_result
                        ),
                        "sources": [],
                    }
                else:
                    answer = st.session_state.chat_service.ask(prompt)
            except (TypeError, ValueError, SyntaxError, ZeroDivisionError) as error:
                answer = {
                    "answer": f"Nie udało się wykonać obliczenia: {error}",
                    "sources": [],
                }
                visualization = {}

            st.markdown(answer["answer"])
            if figure is not None:
                st.plotly_chart(figure, use_container_width=True)
            render_message_details(
                {
                    "sources": answer["sources"],
                    "retrieval_metrics": answer.get("retrieval_metrics", {}),
                }
            )
            session_repository.add_message(current_conversation_id, "user", prompt)
            session_repository.add_message(
                current_conversation_id,
                "assistant",
                answer["answer"],
                answer["sources"],
                visualization,
                answer.get("retrieval_metrics", {}),
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer["answer"],
                    "sources": answer["sources"],
                    "visualization": visualization,
                    "retrieval_metrics": answer.get("retrieval_metrics", {}),
                }
            )
            st.rerun()