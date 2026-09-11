# Lista rozwoju aplikacji

## Kierunek rozwoju

Najważniejsza zmiana architektoniczna: aplikacja nie powinna być pojedynczym LLM-em
z doczepionym retrievaliem. Główny model ma pełnić rolę **koordynatora**. Jego zadaniem
jest rozpoznanie celu wiadomości, zebranie brakujących parametrów i wybranie właściwej
ścieżki wykonania. Nie powinien sam wymyślać zadań, źródeł, wyników obliczeń ani
parametrów wywołań narzędzi.

Docelowy przepływ:

```text
wiadomość ucznia
		-> koordynator: intencja + parametry + poziom pewności
		-> walidacja planu
		-> tool deterministyczny albo agent wyspecjalizowany
		-> wynik strukturalny z proweniencją
		-> koordynator: odpowiedź zgodna z rolą i poziomem pomocy
```

Podstawowe zasady:

- **Koordynator** interpretuje cel użytkownika i planuje wykonanie, ale nie zastępuje
	narzędzi matematycznych ani wyszukiwania.
- **Toole** mają jawne schematy wejścia i wyjścia, walidują parametry i zwracają
	dane albo kontrolowaną informację o braku wyniku. Nie generują swobodnych odpowiedzi.
- **Agenci** wykonują zamknięte zadania wieloetapowe, np. przygotowanie autorskiego
	zadania na podstawie kilku zadań CKE. Mogą korzystać z tooli, ale zwracają wynik
	strukturalny z uzasadnieniem i źródłami.
- **Modele** są dobierane do zadania: tani model wystarcza do prostego dialogu,
	a model reasoningowy jest używany dopiero do trudnego planowania, matematyki lub
	kontroli jakości.
- Każdy etap musi rozróżniać treść źródłową, wynik narzędzia, wniosek agenta i tekst
	wygenerowany dla ucznia.

### Priorytety architektury

1. **P0: kontrakty i koordynator** - typy intencji, schemat planu, rejestr tooli,
	 walidacja parametrów, obsługa braku danych i testy routingu. Najpierw zastępuje
	 obecny lokalny router jednym punktem decyzyjnym.
2. **P0: deterministyczne toole informacji** - pobieranie zadań CKE po metadanych,
	 pobieranie odpowiadającego klucza, wymagania i wzory ze stroną źródła. Przy braku
	 parametrów tool prosi o doprecyzowanie albo wybiera jawnie oznaczony losowy wariant,
	 zamiast pozwalać LLM-owi wymyślać zadanie.
3. **P0: toole matematyczne** - SymPy i Plotly jako narzędzia wywoływane według
	 kontraktu, z walidacją wyniku i bez przekazywania modelowi odpowiedzialności za
	 rachunki lub wykres.
4. **P1: agent autorskich zadań** - pobiera zadania referencyjne przez tool, tworzy
	 nowe zadanie zgodne z poziomem i wymaganiami, a następnie przechodzi walidację
	 zakresu, jednoznaczności i rozwiązania.
5. **P1: agent rozwiązań i oceny** - oddzielny wykonawca może analizować treść,
	 korzystać z klucza i narzędzi matematycznych oraz zwracać rozwiązanie lub ocenę
	 w strukturze z krokami, punktami i źródłami.
6. **P2: routing modeli** - tani model dla prostych intencji i prezentacji, model
	 reasoningowy (np. `o3-mini`) dla trudnego planowania, tworzenia zadań i kontroli
	 matematycznej; routing musi mieć limity kosztu, możliwość wymuszenia modelu i log
	 decyzji.

### Kontrakt koordynatora

Koordynator powinien zwracać strukturę z co najmniej:

- `intent`: np. `find_exam_task`, `find_solution`, `explain_requirement`,
	`solve_math`, `create_original_task`, `evaluate_answer`, `plot`;
- `route`: nazwa toola albo agenta;
- `arguments`: wyłącznie parametry zgodne ze schematem wybranej ścieżki;
- `response_mode`: `hint`, `guided`, `full_solution`, `answer_only` albo `clarify`;
- `level`, `source_constraints` i `confidence`;
- `needs_clarification`: informację, czy trzeba zadać pytanie zamiast działać.

Plan koordynatora musi być walidowany przed wykonaniem. Niepoprawny plan, brak
wymaganych parametrów albo niska pewność nie mogą prowadzić do swobodnego zgadywania.

### Kontrakt toola wyszukiwania zadań

Pierwszy tool powinien przyjmować m.in. poziom, rok, miesiąc, termin, typ źródła,
numer zadania i temat. Powinien zwracać treść zadania, identyfikator liścia i grupy,
strony, `source_group_id`, typ źródła oraz potwierdzenie proweniencji. Jeśli filtr
nie daje wyniku, tool może zwrócić kontrolowany wybór losowy z widocznym komunikatem,
ale nie może zmieniać kryteriów po cichu.

### Klasyfikacja zadań i zgodność z toolem

Intencja użytkownika i klasyfikacja zadania to dwa różne pojęcia:

- `intent` opisuje, co użytkownik chce zrobić, np. `find_exam_task`, `solve_math`,
  `create_original_task` albo `evaluate_answer`;
- `topics` i `skills` opisują, czego dotyczy konkretne zadanie, np. funkcji,
  prawdopodobieństwa albo geometrii analitycznej.

Koordynator nie powinien zwracać dowolnego tekstu tematu. Otrzymuje zamknięty słownik
wartości, a tool akceptuje wyłącznie etykiety zgodne z tym słownikiem. Wstępna taksonomia
tematów obejmuje: `liczby_i_dzialania`, `wyrazenia_algebraiczne`,
`rownania_i_nierownosci`, `funkcje`, `ciagi`, `trygonometria`, `geometria_plaska`,
`geometria_analityczna`, `stereometria`, `kombinatoryka`, `prawdopodobienstwo`,
`statystyka`, `pochodne` i `optymalizacja`. Etykiety mogą być wielowartościowe, ponieważ
jedno zadanie może łączyć kilka działów.

Klasyfikację należy przeprowadzić etapami:

1. wyprowadzić sygnały deterministyczne z treści i metadanych;
2. sklasyfikować zadania wsadowo przez model według zamkniętego słownika;
3. zapisać `confidence` i źródło klasyfikacji;
4. ręcznie zweryfikować zadania o niskiej pewności oraz najczęściej używane kategorie.

Klasyfikacja powinna być przechowywana osobno, np. w `data/task_catalog.json`, z kluczem
`source_group_id::task_id`, `classification_version`, listami `topics` i `skills`,
poziomem trudności, pewnością oraz statusem weryfikacji. Nie należy wymuszać przebudowy
embeddingów przy każdej korekcie etykiet; tool może najpierw filtrować po katalogu,
a dopiero potem używać retrieval tekstowego i rerankingu.

## Plan kolejnej iteracji

### Funkcje wynikające z wymagań promptów

- [x] Przenieść prompt bazowy z kodu do zewnętrznego pliku i rozdzielić go od promptów ról.
- [x] Dodać katalog źródeł opisujący zawartość plików, ich zastosowanie i hierarchię wiarygodności.
- [x] Usunąć osobny tryb „podpowiedzi krok po kroku”; stopniowanie podpowiedzi należy do tutora.
- [x] Uporządkować `data/` według poziomu matury oraz typów materiałów: wymagania, karta wzorów, informatory, arkusze i klucze.
- [x] Dodać identyfikatory źródłowych zadań: poziom, rok, miesiąc, typ dokumentu, grupę zadania, numer zadania i listę stron.
- [x] Dodać metadane dokumentów: poziom, rok, typ źródła, proweniencję oraz status potwierdzenia źródła.
- [x] Wymuszać przekazywanie wybranej roli do każdej ścieżki generowania odpowiedzi, także do wyjaśnień narzędzi matematycznych.
- [x] Jawnie obsługiwać brakujące wykresy, rysunki i tabele: nie zgadywać ich treści i prosić o obraz lub dane, gdy są konieczne.
- [ ] Dodać strukturalny profil ucznia: poziom przygotowania, preferowana szczegółowość i bieżący tryb pracy.
- [ ] Dodać walidację, czy zadanie lub generowany przykład mieści się w aktualnych wymaganiach dla poziomu ucznia.
- [ ] Rozdzielić oficjalną punktację CKE od nieoficjalnej oceny szacunkowej wywnioskowanej z analogii.
- [ ] Zapisywać błędy i słabe działy ucznia jako sygnały do dalszej nauki, bez zastępowania nimi bieżącej oceny.
- [x] Filtrować i rerankować retrieval według poziomu i typu źródła przed przekazaniem kontekstu LLM.
- [x] Rozdzielić arkusz i klucz kontrolnej matury rozszerzonej na logiczne zadania i podzadania z zachowaniem wspólnego identyfikatora pary.
- [ ] Zastąpić lokalny router koordynatorem zwracającym walidowany plan intencji, toola/agenta, parametrów, poziomu pewności i trybu odpowiedzi.
- [ ] Zdefiniować wspólne schematy `ToolRequest`, `ToolResult`, `AgentRequest`, `AgentResult` i `ResponsePlan`.
- [ ] Dodać rejestr tooli z walidacją schematów, limitami czasu/kosztu i bezpieczną obsługą błędów.
- [ ] Dodać deterministyczny tool wyszukiwania zadań CKE po metadanych, z kontrolowanym wyborem losowym przy braku kompletu filtrów.
- [ ] Zdefiniować zamknięty, wieloetykietowy słownik `topics` i `skills` wspólny dla koordynatora, katalogu zadań i toola wyszukiwania.
- [ ] Zbudować `task_catalog.json` z klasyfikacją zadań po `source_group_id::task_id`, wersją klasyfikacji, confidence i statusem weryfikacji.
- [ ] Sklasyfikować zadania etapami: sygnały deterministyczne, klasyfikacja wsadowa, kontrola confidence i ręczna weryfikacja próby.
- [ ] Dodać osobne toole pobierania klucza, wymagań i wzorów ze stroną oraz powiązaniem proweniencji.
- [ ] Dodać osobny przepływ generowania zadań z kontrolą zakresu, poziomu, rozwiązania i oznaczeniem zadania jako własnego.
- [ ] Wydzielić agenta tworzenia autorskich zadań, który korzysta z zadań referencyjnych wyłącznie przez tool.
- [ ] Dodać opcjonalny model reasoningowy (np. `o3-mini`) oraz routing modeli: droższy model do trudnego planowania, matematyki i kontroli jakości, tańszy model do prostych pytań i prezentacji.

### Etap 1: stabilizacja i jakość

- [x] Usunąć zdublowany stary przepływ z `app.py`.
- [x] Dodać testy promptów, SQLite i wykrywania zmian indeksu.
- [x] Zainstalować zależności testowe i uruchomić pełny `pytest` w środowisku projektu.
- [x] Dodać test aplikacyjny sprawdzający tworzenie i przełączanie sesji.

### Etap 2: jakość danych RAG

- [x] Wydzielić parser PDF oparty na stronach i sekcjach.
- [x] Zachować `file_name`, numer strony, typ dokumentu i tytuł sekcji w metadanych fragmentów.
- [x] Ograniczać kontekst odpowiedzi przez retriever z pulą 150 kandydatów i przekazywać dalej tylko wynik rerankingu, zamiast cały indeks do LLM; zwykłe pytania dostają 6 fragmentów, a pytania o pełny zakres wymagań wszystkie znalezione bloki wymagań.
- [x] Dodać konfigurowalny próg podobieństwa i odrzucać fragmenty, które nie są wystarczająco trafne.
- [x] Usunąć stały threshold podobieństwa wektorów i zastąpić go rerankingiem leksykalno-metadanych.
- [ ] Dobrać rozmiar i overlap chunków na podstawie pomiarów jakości oraz kosztu tokenów.
- [x] Ustawić jawny `SentenceSplitter` z konfigurowalnym rozmiarem i overlapem oraz unieważniać indeks po zmianie tych parametrów.
- [x] Mierzyć liczbę pobranych fragmentów, długość kontekstu i przybliżenie tokenów; koszt zapytania pozostaje do połączenia z usage API modelu.
- [ ] Pomijać kondensowanie historii dla niezależnych pytań, aby uniknąć dodatkowego wywołania LLM.
- [x] Dodać router decydujący, czy pytanie wymaga RAG, narzędzia matematycznego czy odpowiedzi bez retrieval.
- [ ] Przenieść decyzję o użyciu RAG, toola lub agenta do koordynatora LLM z walidowanym planem.
- [ ] Rejestrować plan koordynatora, wywołania tooli, wyniki pośrednie i końcową proweniencję bez ujawniania surowego toku rozumowania.
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
- [ ] Dodać routing modeli z opcjonalnym modelem reasoningowym (np. `o3-mini`) dla zadań wymagających głębszego rozumowania, z zachowaniem tańszego modelu dla prostych zapytań.
- [ ] Dodać możliwość ręcznego wymuszenia modelu oraz limity kosztu i fallback po błędzie modelu.

## Interfejs i formatowanie

- [x] Dodać możliwość usuwania istniejących chatów z historii.
- [x] Zapewnić, że w historii może istnieć tylko jeden pusty chat; przycisk „Nowy chat” nie powinien tworzyć kolejnych pustych rozmów.
- [x] Umożliwić nadawanie chatowi własnej nazwy przez użytkownika, niezależnie od treści zapytań.
- [ ] Ukryć mały przycisk kotwicy/linku wyświetlany przy tytule aplikacji, jeśli nie pełni funkcji użytkowej.
- [ ] W ramce "Nazwa chatu" z defaultu pokazywać tylko napis na szaro, niemodyfikowalny "Zmień nazwę", ponieważ zarówno w liście rozwijanej jak i w ramce na zmianę nazwy wyświetla się to samo, co jest mylące dla użytkownika
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
- [ ] Udostępnić RAG jako deterministyczny tool zwracający ustrukturyzowane fragmenty, metadane i proweniencję, zamiast traktować go jako domyślną odpowiedź.
- [ ] Dodać tool wyszukiwania konkretnego zadania po `level`, `year`, `month`, `term`, `task_id`, `topic` i `source_kind`.
- [ ] Dodać tool pobierania pary zadanie-klucz po `source_group_id` i `task_id`.
- [ ] Wyszukiwanie hybrydowe: wektory plus BM25.
- [ ] Reranking wyników po wstępnym retrieval, np. dopiero dla pytań wymagających większej precyzji.
- [ ] Parser tabel zachowujący układ punktacji CKE.
- [x] Parsować PDF stronami, pomijać puste strony i zachować podstawową strukturę sekcji.

## Infrastruktura i optymalizacja

- [ ] Historia czatu i logi w SQLite.
- [ ] Monitoring tokenów i kosztów per sesja.
- [ ] Rate limiting.
- [ ] Konfigurowalny katalog danych i indeksów dla wdrożeń.
