import os
from dotenv import load_dotenv
import streamlit as st
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Settings, 
    StorageContext, 
    load_index_from_storage
)
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Domyślnie wybrany model LOKALNY (darmowy) - pierwsza pozycja na liście
embed_mode = st.sidebar.radio(
    "Silnik wektoryzacji:", 
    ["Lokalny (BAAI/bge-small-en-v1.5)", "OpenAI (text-embedding-3-small)"]
)

if embed_mode == "OpenAI (text-embedding-3-small)":
    PERSIST_DIR = "./storage_openai"
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
else:
    PERSIST_DIR = "./storage_local"
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Automatyczne ładowanie klucza API z pliku .env
load_dotenv()

PERSIST_DIR = "./storage"  # Folder na zapisaną bazę wektorową

st.set_page_config(page_title="Tutor Maturalny CKE", page_icon="📐", layout="centered")
st.title("📐 Tutor CKE - Matura z Matematyki")

SYSTEM_PROMPT = """
Jesteś profesjonalnym tutorem i egzaminatorem CKE z matematyki. 
Odpowiadaj na pytania ucznia wyłącznie w oparciu o dostarczone materiały (Karta Wzorów, Informatory CKE, Zasady Oceniania).
Jeśli podajesz wzór, podawaj dokładny dział z Karty Wzorów CKE.
Gdy oceniasz zadanie, stosuj oficjalne kryteria punktowania CKE (etap postępu, pokonanie zasadniczych trudności).
"""

@st.cache_resource(show_spinner=False)
def create_or_load_index(persist_dir, mode_name):
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)
    
    index_file = os.path.join(persist_dir, "docstore.json")
    if not os.path.exists(index_file):
        with st.spinner(f"Tworzenie bazy ({mode_name})... To może potrwać."):
            documents = SimpleDirectoryReader(input_dir="./data", recursive=True).load_data()
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=persist_dir)
            return index
    else:
        with st.spinner(f"Wczytywanie bazy wektorowej ({mode_name})..."):
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            return load_index_from_storage(storage_context)

# ZABEZPIECZENIE PRZED AUTOMATYCZNYM GENEROWANIEM
index_file_path = os.path.join(PERSIST_DIR, "docstore.json")

if os.path.exists(index_file_path):
    # Wczytywanie istniejącej bazy
    index = create_or_load_index(PERSIST_DIR, embed_mode)
else:
    # Zatrzymanie aplikacji i wymuszenie zgody na generowanie
    st.warning(f"Brak bazy danych w folderze {PERSIST_DIR}.")
    
    if st.button(f"Wygeneruj bazę dla: {embed_mode}"):
        index = create_or_load_index(PERSIST_DIR, embed_mode)
        st.rerun()
        
    st.stop()

# Tworzenie chatu z pamięcią konwersacji
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", 
        verbose=True
    )

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
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            st.session_state.messages.append({"role": "assistant", "content": response.response})