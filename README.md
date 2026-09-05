# 📐 Asystent Maturalny z Matematyki (RAG)

Lokalna aplikacja wspierająca naukę do matury z matematyki (poziom podstawowy i rozszerzony) w oparciu o oficjalne wytyczne, Kartę Wzorów oraz zasady oceniania Centralnej Komisji Egzaminacyjnej (CKE).

Aplikacja wykorzystuje framework **LlamaIndex** do przeszukiwania bazy dokumentów (RAG) oraz interfejs **Streamlit**.

---

## 🚀 Szybki start (Uruchomienie aplikacji)

Za każdym razem, gdy chcesz uruchomić aplikację, otwórz **Anaconda Prompt** i wykonaj poniższe kroki:

### 1. Przejdź do folderu projektu

```bash
cd C:\sciezka\do\twojego\folderu\matura_ai
```

### 2. Aktywuj środowisko Conda

```bash
conda activate matura_rag
```

### 3. Uruchom aplikację Streamlit

```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie w Twojej przeglądarce pod adresem `http://localhost:8501`.

---

## 📁 Struktura projektu

* **`data/`** – folder na źródłowe pliki PDF z CKE (Karta Wzorów, Informatory, Zasady Oceniania).
* **`storage/`** – folder generowany automatycznie. Przechowuje przetworzoną bazę wektorową (`docstore.json` itp.), co eliminuje konieczność ponownego indeksowania plików przy każdym uruchomieniu.
* **`.env`** – plik konfiguracyjny przechowujący klucz API (`OPENAI_API_KEY=sk-...`).
* **`app.py`** – główny kod źródłowy aplikacji (logika RAG + interfejs).

---

## 🔄 Odświeżanie bazy wiedzy (Dodawanie nowych plików PDF)

Aplikacja automatycznie wczytuje zapisaną bazę wektorową z folderu `./storage`.

Jeśli dodasz nowe pliki PDF do folderu `./data` i chcesz, aby bot zaczął z nich korzystać:

1. Zamknij aplikację (`Ctrl + C` w Anaconda Prompt).
2. **Usuń pliki z folderu `storage/`** (lub skasuj cały folder).
3. Uruchom aplikację ponownie (`streamlit run app.py`). System przy pierwszym uruchomieniu zbuduje nową indeksację.

---

## 🛠️ Wymagania i instalacja (Jednorazowa konfiguracja)

Jeśli uruchamiasz projekt na nowym komputerze:

### 1. Tworzenie środowiska

```bash
conda create -n matura_rag python=3.11 -y
conda activate matura_rag
```

### 2. Instalacja bibliotek

```bash
pip install llama-index streamlit pypdf openai python-dotenv
```

### 3. Utworzenie pliku `.env` z kluczem OpenAI

```bash
echo OPENAI_API_KEY=twoj_klucz_api > .env
```
