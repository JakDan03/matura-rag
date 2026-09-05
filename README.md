# Asystent Maturalny z Matematyki (RAG)

Lokalna aplikacja Streamlit wspierająca naukę do matury z matematyki na podstawie materiałów CKE. Wykorzystuje LlamaIndex do wyszukiwania dokumentów i OpenAI do generowania odpowiedzi. Embeddingi mogą być tworzone lokalnie albo przez OpenAI.

## Uruchomienie

W środowisku Python 3.11:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Na Condzie można użyć:

```bash
conda create -n matura_rag python=3.11 -y
conda activate matura_rag
pip install -r requirements.txt
streamlit run app.py
```

Wymagany jest plik `.env` z kluczem:

```text
OPENAI_API_KEY=twoj_klucz_api
```

## Struktura projektu

```text
app.py                         # Entry point i warstwa Streamlit
config/settings.py             # Ścieżki i ustawienia modeli
config/prompts/                # Role i prompty w plikach tekstowych
src/prompts/                   # Ładowanie i składanie promptów
src/rag/                       # Modele, parser PDF i zarządzanie indeksami
src/services/                  # Usługi aplikacyjne, obecnie czat
src/storage/                   # Repozytorium historii rozmów SQLite
tests/                         # Testy modułów aplikacji
data/                          # Źródłowe pliki PDF CKE
storage/indexes/               # Trwałe indeksy rozdzielone według embeddingu
new_features.md                # Checklista dalszego rozwoju
.streamlit/config.toml         # Ustawienia uruchomienia Streamlit
```

## Uwagi o uruchomieniu

Projekt wyłącza introspekcję pakietów przez Streamlit Watcher w `.streamlit/config.toml`. Biblioteka `transformers` udostępnia opcjonalne moduły wizji, które bez zainstalowanego `torchvision` generują tracebacki watchera, mimo że tekstowe embeddingi działają poprawnie. Obecna aplikacja używa embeddingów tekstowych, więc `torchvision` nie jest potrzebne.

## Indeksowanie dokumentów

Po wybraniu silnika wektoryzacji aplikacja szuka indeksu w odpowiednim katalogu:

```text
storage/indexes/local/bge-small-en-v1.5/
storage/indexes/openai/text-embedding-3-small/
```

Przy pierwszym uruchomieniu trzeba kliknąć przycisk tworzenia bazy. PDF-y są parsowane stronami przez `pypdf`; każda niepusta strona staje się dokumentem z metadanymi nazwy pliku, numeru strony, typu dokumentu i sekcji. Indeks zapisuje także metadane parsera i hash plików z `data/`. Po dodaniu lub zmianie PDF albo zmianie wersji parsera aplikacja wykryje nieaktualność i pozwoli utworzyć nową wersję. Indeksy nie powinny być przechowywane w repozytorium, dlatego katalog `storage/` jest ignorowany przez Git.

## Prompty i role

Role znajdują się w `config/prompts/roles.json`, a ich treść w plikach Markdown obok niego. Obecnie dostępne są role tutora, egzaminatora i trybu podpowiedzi. Kontekst ucznia można podać w panelu bocznym; jest dołączany do promptu sesji.

## Testy i dalszy rozwój

Kontrolę składni można wykonać poleceniem:

```bash
python -m compileall -q app.py config src
```

## Historia rozmów i źródła

Historia rozmów jest zapisywana lokalnie w `storage/sessions.sqlite3`. Z panelu bocznego można utworzyć nową rozmowę albo przełączyć się na wcześniejszą. Odpowiedzi pokazują dostępne źródła dokumentowe, w tym numer strony, jeśli parser i indeks zachowały takie metadane.

## Testy

Po instalacji zależności uruchom:

```bash
python -m pytest -q
```

Plan funkcji znajduje się w [new_features.md](new_features.md). Następne etapy to parser PDF zachowujący strukturę, lepsze cytowania, renderowanie LaTeX i narzędzia SymPy.
