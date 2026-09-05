### Zarządzanie promptami i modelem
- Zewnętrzne pliki konfiguracyjne (np. .json, .yaml) na prompty systemowe, oddzielające logikę od tekstu.
- Interfejs (UI) do edycji promptów systemowych i wytycznych w locie, bez dotykania kodu.
- Biblioteka gotowych ról (np. "Surowy egzaminator", "Cierpliwy tłumacz z podpowiedziami krok po kroku").
- Dynamiczne wstrzykiwanie kontekstu ucznia do promptu (np. poziom trudności, preferowana metoda rozwiązywania).
- Suwak parametryzacji modelu (temperatura, Top-P) w panelu bocznym. Ewentualnie – dostosowanie temperatury w zależności od zadania/agenta, ale nie przez uzytkownika

### Interfejs i formatowanie (UI/UX)
- Interpretacja i poprawne renderowanie wzorów matematycznych (wymuszenie formatowania MathJax/LaTeX przez st.latex()).
- Przycisk "Pokaż tok rozumowania" rozwijający (w akordeonie st.expander) matematyczne kroki.
- Zapisywanie, ładowanie i usuwanie historii sesji konwersacji.
- Eksport rozmowy lub wygenerowanego arkusza do PDF/Markdown.
- Wbudowana przeglądarka dokumentów (np. podgląd wycinka Karty Wzorów obok czatu).
Obliczenia, kodowanie i wizualizacja
- Moduł wykonywania kodu Python (sandbox) do precyzyjnych obliczeń algebaicznych (eliminacja halucynacji matematycznych).
- Integracja z matplotlib / plotly do interaktywnego rysowania wykresów funkcji z poziomu czatu.
- Wykorzystanie biblioteki sympy do symbolicznego rozwiązywania równań, całek i pochodnych.

### Narzędzia dla korepetytora i ucznia
- Profile uczniów (śledzenie historii błędów, postępów i statystyk słabych działów).
- Moduł generowania spersonalizowanych kartkówek i zadań domowych z wybranych tematów.
- Wgrywanie zdjęć lub zrzutów ekranu zadań (OCR z wykorzystaniem modeli wizyjnych, np. gpt-4o).

### Rozbudowa RAG (Retrieval-Augmented Generation)
- Wskazywanie precyzyjnych źródeł (np. "Karta Wzorów, strona 4" z linkiem do pobranego fragmentu).
- Wyszukiwanie hybrydowe (wektory + słowa kluczowe BM25) dla wyższej precyzji wyszukiwania samych wzorów.
- Reranking (np. Cohere Rerank) odrzucający mało trafne fragmenty informatorów.
- Dedykowany parser tabel (np. LlamaParse), zachowujący układ punktacji CKE.

### Infrastruktura i optymalizacja
- Zapis historii czatu i logów do lokalnej bazy danych SQLite.
- Monitoring zużycia tokenów i kosztów z podziałem na poszczególne sesje.
- Zabezpieczenie limitu zapytań (rate limiting), aby unikać przypadkowego przekroczenia budżetu.
- Konteneryzacja aplikacji (Docker) do łatwego przenoszenia środowiska między komputerami.

### Dodatkowo (priorytetowo)
- Bug: nie zapisały mi się wygenerowane wektory
- Automatyczne testy funkcjonalności aplikacji
- Plik, który będzie przykładem pliku .env – do skopiowania dla użytkownika
