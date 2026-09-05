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
- [x] Ograniczać kontekst odpowiedzi przez retriever `similarity_top_k=2`, zamiast przekazywać cały indeks do LLM.
- [x] Dodać konfigurowalny próg podobieństwa i odrzucać fragmenty, które nie są wystarczająco trafne.
- [ ] Dobrać rozmiar i overlap chunków na podstawie pomiarów jakości oraz kosztu tokenów.
- [x] Mierzyć liczbę pobranych fragmentów, długość kontekstu i przybliżenie tokenów; koszt zapytania pozostaje do połączenia z usage API modelu.
- [ ] Pomijać kondensowanie historii dla niezależnych pytań, aby uniknąć dodatkowego wywołania LLM.
- [x] Dodać router decydujący, czy pytanie wymaga RAG, narzędzia matematycznego czy odpowiedzi bez retrieval.
- [x] Dodać walidację indeksu i bezpieczną przebudowę do katalogu tymczasowego.
- [x] Dodać opcjonalny eksport sparsowanych dokumentów do czytelnych plików diagnostycznych, np. tekstu per strona i `manifest.json` z metadanymi.
- [ ] Renderować cytowania jako klikalne źródła, gdy dostępny jest podgląd dokumentu.

### Etap 3: doświadczenie ucznia

- [x] Renderować odpowiedzi z LaTeX bez traktowania całego tekstu jako wzoru.
- [ ] Dodać eksport rozmowy do Markdown.
- [x] Dodać usuwanie sesji oraz tytuły rozmów edytowalne przez użytkownika.
- [ ] Dodać kontrolowany widok kroków rozwiązania zamiast ujawniania surowego rozumowania modelu.

### Etap 4: narzędzia matematyczne

- [x] Dodać SymPy jako jawne narzędzie do weryfikacji rachunków.
- [x] Dodać wykresy funkcji 2D i 3D przez Plotly z ograniczonym zakresem próbkowania.
- [ ] W późniejszym etapie zastąpić techniczne polecenia typu `wykres 2d: sin(x)` rozpoznawaniem intencji i parametrów z naturalnego kontekstu rozmowy; po wdrożeniu routera usunąć ten tryb z interfejsu użytkownika.
- [ ] W późniejszym etapie zastąpić techniczną składnię `rozwiąż: ...` / `solve: ...` rozpoznawaniem próśb o rozwiązanie równań z naturalnego języka i kierowaniem ich przez router narzędzi do `MathService`.
- [ ] Zastąpić specjalny przypadek `circle` generycznym opisem sceny geometrycznej: figury, punkty, odcinki, etykiety, współrzędne i relacje odczytywane z treści zadania; obecny okrąg pozostaje tylko kompatybilnością przejściową.
- [ ] Docelowo wdrożyć agenta planującego wizualizację: agent analizuje naturalną treść zadania i generuje zwalidowany `VisualizationSpec`, natomiast deterministyczny `PlotService` renderuje scenę przez Plotly. Agent nie powinien generować ani wykonywać dowolnego kodu ani obrazu bezpośrednio.
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

- [x] Dodać możliwość usuwania istniejących chatów z historii.
- [x] Zapewnić, że w historii może istnieć tylko jeden pusty chat; przycisk „Nowy chat” nie powinien tworzyć kolejnych pustych rozmów.
- [x] Umożliwić nadawanie chatowi własnej nazwy przez użytkownika, niezależnie od treści zapytań.
- [ ] Ukryć mały przycisk kotwicy/linku wyświetlany przy tytule aplikacji, jeśli nie pełni funkcji użytkowej.
- [x] Dodać klikalny przycisk zatwierdzania preferencji użytkownika zamiast wymagać skrótu klawiszowego.
- [x] Poprawne renderowanie wzorów jako LaTeX.
- [ ] Przycisk „Pokaż tok rozumowania” w kontrolowanym widoku kroków.
- [x] Zapisywanie i ładowanie historii sesji w SQLite.
- [x] Usuwanie historii sesji z interfejsu.
- [ ] Eksport rozmowy i arkuszy do PDF/Markdown.
- [ ] Przeglądarka dokumentów z podglądem źródła obok czatu.

## Obliczenia, kodowanie i wizualizacja

- [ ] Bezpieczny sandbox do obliczeń Python.
- [x] Wykresy funkcji przez Plotly.
- [x] Narzędzie SymPy do obliczeń symbolicznych.

## Narzędzia dla korepetytora i ucznia

- [ ] Profile uczniów i statystyki słabych działów.
- [ ] Generator spersonalizowanych kartkówek i prac domowych.
- [ ] Wgrywanie zdjęć zadań i OCR.

## Rozbudowa RAG

- [x] Wyświetlanie źródeł odpowiedzi z nazwą pliku i numerem strony, gdy metadane są dostępne.
- [ ] Wyszukiwanie hybrydowe: wektory plus BM25.
- [ ] Reranking wyników po wstępnym retrieval, np. dopiero dla pytań wymagających większej precyzji.
- [ ] Parser tabel zachowujący układ punktacji CKE.
- [x] Parsować PDF stronami, pomijać puste strony i zachować podstawową strukturę sekcji.

## Infrastruktura i optymalizacja

- [ ] Historia czatu i logi w SQLite.
- [ ] Monitoring tokenów i kosztów per sesja.
- [ ] Rate limiting.
- [ ] Konfigurowalny katalog danych i indeksów dla wdrożeń.
