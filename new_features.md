# Lista rozwoju aplikacji

## Plan kolejnej iteracji

### Etap 1: stabilizacja i jakość

- [x] Usunąć zdublowany stary przepływ z `app.py`.
- [x] Dodać testy promptów, SQLite i wykrywania zmian indeksu.
- [x] Zainstalować zależności testowe i uruchomić pełny `pytest` w środowisku projektu.
- [x] Dodać test aplikacyjny sprawdzający tworzenie i przełączanie sesji.

### Etap 2: jakość danych RAG

- [x] Wydzielić parser PDF oparty na stronach i sekcjach.
- [x] Zachować `file_name`, numer strony, typ dokumentu i tytuł sekcji w metadanych fragmentów.
- [ ] Dodać walidację indeksu i bezpieczną przebudowę do katalogu tymczasowego.
- [ ] Renderować cytowania jako klikalne źródła, gdy dostępny jest podgląd dokumentu.

### Etap 3: doświadczenie ucznia

- [ ] Renderować odpowiedzi z LaTeX bez traktowania całego tekstu jako wzoru.
- [ ] Dodać eksport rozmowy do Markdown.
- [ ] Dodać usuwanie sesji oraz tytuły rozmów edytowalne przez użytkownika.
- [ ] Dodać kontrolowany widok kroków rozwiązania zamiast ujawniania surowego rozumowania modelu.

### Etap 4: narzędzia matematyczne

- [ ] Dodać SymPy jako jawne narzędzie do weryfikacji rachunków.
- [ ] Dodać wykresy funkcji z ograniczeniem zakresu i czasu obliczeń.
- [ ] Dopiero po testach narzędzi rozważyć izolowany sandbox kodu Python.

### Kryterium ukończenia iteracji

Iteracja jest gotowa, gdy aplikacja ma powtarzalny parser PDF z metadanymi stron, testy uruchamiane jedną komendą, trwałe sesje z pełnym CRUD oraz odpowiedzi prezentujące źródła i wzory w czytelny sposób.

## Architektura i fundamenty

- [x] Rozdzielenie entrypointu Streamlit od logiki RAG i obsługi czatu.
- [x] Zewnętrzne pliki promptów i biblioteka ról.
- [x] Wydzielenie konfiguracji aplikacji i fabryki modeli.
- [x] Osobne katalogi indeksów dla lokalnego i OpenAI embeddingu.
- [x] Zapisywanie metadanych indeksu oraz wykrywanie zmian w plikach źródłowych.
- [x] Plik `requirements.txt` z zależnościami instalowanymi jedną komendą.
- [x] Automatyczne testy modułów promptów, sesji i managera indeksu.
- [ ] Konteneryzacja aplikacji (Docker).

## Zarządzanie promptami i modelem

- [x] Zewnętrzne pliki konfiguracyjne promptów.
- [x] Biblioteka gotowych ról: tutor, egzaminator, podpowiedzi.
- [x] Dynamiczne wstrzykiwanie kontekstu ucznia.
- [ ] UI do edycji promptów systemowych i wytycznych.
- [ ] Suwak temperatury i Top-P w panelu bocznym.
- [ ] Automatyczny dobór parametrów modelu do zadania.

## Interfejs i formatowanie

- [ ] Dodać możliwość usuwania istniejących chatów z historii.
- [ ] Zapewnić, że w historii może istnieć tylko jeden pusty chat; przycisk „Nowy chat” nie powinien tworzyć kolejnych pustych rozmów.
- [ ] Umożliwić nadawanie chatowi własnej nazwy przez użytkownika, niezależnie od treści zapytań.
- [ ] Ukryć mały przycisk kotwicy/linku wyświetlany przy tytule aplikacji, jeśli nie pełni funkcji użytkowej.
- [ ] Dodać klikalny przycisk zatwierdzania preferencji użytkownika zamiast wymagać skrótu klawiszowego.
- [ ] Poprawne renderowanie wzorów jako LaTeX.
- [ ] Przycisk „Pokaż tok rozumowania” w kontrolowanym widoku kroków.
- [x] Zapisywanie i ładowanie historii sesji w SQLite.
- [ ] Usuwanie historii sesji z interfejsu.
- [ ] Eksport rozmowy i arkuszy do PDF/Markdown.
- [ ] Przeglądarka dokumentów z podglądem źródła obok czatu.

## Obliczenia, kodowanie i wizualizacja

- [ ] Bezpieczny sandbox do obliczeń Python.
- [ ] Wykresy funkcji przez matplotlib lub Plotly.
- [ ] Narzędzie SymPy do obliczeń symbolicznych.

## Narzędzia dla korepetytora i ucznia

- [ ] Profile uczniów i statystyki słabych działów.
- [ ] Generator spersonalizowanych kartkówek i prac domowych.
- [ ] Wgrywanie zdjęć zadań i OCR.

## Rozbudowa RAG

- [x] Wyświetlanie źródeł odpowiedzi z nazwą pliku i numerem strony, gdy metadane są dostępne.
- [ ] Wyszukiwanie hybrydowe: wektory plus BM25.
- [ ] Reranking wyników.
- [ ] Parser tabel zachowujący układ punktacji CKE.
- [x] Parsować PDF stronami, pomijać puste strony i zachować podstawową strukturę sekcji.

## Infrastruktura i optymalizacja

- [ ] Historia czatu i logi w SQLite.
- [ ] Monitoring tokenów i kosztów per sesja.
- [ ] Rate limiting.
- [ ] Konfigurowalny katalog danych i indeksów dla wdrożeń.
