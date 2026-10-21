from __future__ import annotations

import json
import re
from typing import Any

from src.tools.contracts import ToolResult, ToolStatus


class ToolResponseService:
    """Cleans extracted task text for presentation to the student."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def present(self, question: str, result: ToolResult) -> str:
        if result.status != ToolStatus.OK:
            return result.message

        data = result.data if isinstance(result.data, dict) else {}
        metadata = data.get("metadata", {})
        payload = json.dumps(
            {
                "task_text": data.get("content", ""),
                "source": {
                    key: metadata.get(key)
                    for key in (
                        "file_name",
                        "year",
                        "month",
                        "level",
                        "task_id",
                        "page_label",
                    )
                },
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        prompt = f"""Jesteś redaktorem tekstu zadań maturalnych wyekstrahowanego z PDF.
Przygotuj dla ucznia czytelną, kompletną treść wybranego zadania. Nie rozwiązuj go
i nie odpowiadaj merytorycznie na pierwotne pytanie użytkownika; służy ono wyłącznie
jako kontekst wyboru zadania.

Możesz:
- poprawić łamanie wierszy i odstępy;
- usunąć techniczny nagłówek [ŹRÓDŁO: ...] oraz oczywiste stopki, np. "Brudnopis",
  "Więcej arkuszy znajdziesz na stronie", numer strony i kod arkusza;
- uporządkować wzory, ułamki i współrzędne, jeśli ich zamierzony zapis wynika
  jednoznacznie z pozostałego tekstu.

Zachowaj pełną treść polecenia oraz kontekst zadania głównego potrzebny do
zrozumienia podzadania. Zachowaj tabele i wszystkie źródłowe warianty odpowiedzi,
niezależnie od ich liczby i oznaczeń (np. A-D lub A-F); nie twórz brakujących
wariantów. Nie zmieniaj wartości liczbowych, warunków ani sensu polecenia i nie
dopowiadaj informacji.

Zapisuj wzory i symbole matematyczne w poprawnym LaTeX-u, używając delimitera
inline $...$ lub blokowego $$...$$. Zachowuj zakres ułamków, potęg i indeksów
zgodny ze źródłem. Jednoznaczny zapis "n choose k" oznacza symbol Newtona i należy
zapisać go jako $\\binom{{n}}{{k}}$. Strzałkę wektora zapisuj nad całym oznaczeniem,
np. $\\overrightarrow{{AM}}$, nie nad ostatnią literą. Zachowuj znaczenie długości
odcinków, wartości bezwzględnej, kątów, logarytmów, pierwiastków i funkcji
trygonometrycznych. Nie rekonstruuj wzoru na podstawie samego domysłu; gdy zapis
pozostaje niejednoznaczny, zachowaj go bez zmian i oznacz [nieczytelny zapis
w ekstrakcji].

Fragment oznaczony [tu powinien być rysunek] jest adnotacją o brakującej grafice,
a nie częścią polecenia. Nie odtwarzaj rysunku ani nie zgaduj jego zawartości.
Usuń tę adnotację i zastąp ją krótką informacją: "Uwaga: rysunek nie jest
dostępny w ekstrakcji."

Zachowaj wskazówki, które występują w źródle, w tym ich oznaczenie "Wskazówka:".
Nie twórz nowych wskazówek ani rozwiązania.

Zwróć wyłącznie treść zadania. Nie dodawaj rozwiązania, własnej odpowiedzi,
komentarza o wymaganiach ani informacji o źródle; aplikacja pokazuje źródło osobno.

Ustrukturyzowany wynik narzędzia:
{payload}

Pytanie użytkownika (wyłącznie kontekst):
{question}
"""
        response = normalize_latex(str(self.llm.complete(prompt)))
        origin = data.get("origin")
        origin_labels = {
            "official_exam_task": "autentyczne zadanie z arkusza CKE",
            "official_scoring_guide": "oficjalny klucz odpowiedzi CKE",
            "adapted_task": "zadanie zaadaptowane",
            "original_task": "zadanie autorskie",
        }
        if origin in origin_labels:
            selection = " Losowy wybór spośród pasujących zadań." if result.random_selection else ""
            return f"Typ materiału: {origin_labels[origin]}.{selection}\n\n{response}"
        return response


def normalize_latex(text: str) -> str:
    """Convert common LLM math delimiters to Streamlit-friendly Markdown."""

    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text, flags=re.DOTALL)
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    return re.sub(
        r"\((\s*(?:\\(?:sqrt|frac|cdot|times|leq|geq|pi|infty|left|right)\b|\d)[^()\n]*?)\)",
        r"$\1$",
        text,
    )


def source_records(result: ToolResult) -> list[dict[str, Any]]:
    """Converts tool provenance metadata to the UI source shape."""

    sources = []
    for metadata in result.provenance:
        sources.append(
            {
                "file": metadata.get("file_name", "Nieznany dokument"),
                "page": metadata.get("page_label") or metadata.get("page_number"),
                "score": None,
                "document_type": metadata.get("document_type"),
                "level": metadata.get("level"),
                "year": metadata.get("year"),
                "month": metadata.get("month"),
                "term": metadata.get("term"),
                "task_id": metadata.get("task_id"),
                "parent_task_id": metadata.get("parent_task_id"),
                "task_group_id": metadata.get("task_group_id"),
                "page_numbers": metadata.get("page_numbers"),
                "source_group_id": metadata.get("source_group_id"),
                "provenance_confirmed": metadata.get("provenance_confirmed", False),
            }
        )
    return sources
