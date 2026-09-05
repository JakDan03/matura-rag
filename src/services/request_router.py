from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from src.services.math_service import MathService


class RequestRoute(str, Enum):
    MATH = "math"
    PLOT = "plot"
    RAG = "rag"


@dataclass(frozen=True)
class RoutedRequest:
    route: RequestRoute
    payload: str = ""
    plot_type: str | None = None


class RequestRouter:
    """Routes explicit and common natural-language math requests locally."""

    # TODO: Replace plot_type/payload with a validated VisualizationSpec.
    # The future schema should describe a complete scene: objects (figures,
    # points, lines, vectors), coordinates, labels, constraints and relations.
    # The LLM/router should extract that scene from the task statement, while
    # PlotService should only validate and render it.

    _plot_words = re.compile(r"\b(narysuj|rysuj|wykres|wykreśl|pokaż wykres)\b", re.IGNORECASE)
    _circle_words = re.compile(r"\b(okrąg|koło)\b", re.IGNORECASE)
    _solve_words = re.compile(
        r"\b(rozwiąż|rozwiązać|rozwiązanie|oblicz|wyznacz|solve)\b", re.IGNORECASE
    )

    def route(self, question: str) -> RoutedRequest:
        plot_request = MathService.extract_tool_request(question)
        if plot_request:
            plot_type, payload = plot_request
            return RoutedRequest(RequestRoute.PLOT, payload, plot_type)

        if self._plot_words.search(question):
            if self._circle_words.search(question):
                # TODO: Keep this only as a compatibility fallback until the
                # generic geometry-scene router is implemented.
                return RoutedRequest(RequestRoute.PLOT, "unit", "circle")
            expression = self._extract_function_expression(question)
            if expression:
                dimensions = "3d" if re.search(r"\by\b", expression) else "2d"
                return RoutedRequest(RequestRoute.PLOT, expression, dimensions)

        if MathService.is_solve_request(question):
            return RoutedRequest(
                RequestRoute.MATH,
                MathService.extract_solve_expression(question),
            )

        if self._solve_words.search(question) and self._looks_like_equation(question):
            expression = self._extract_equation(question)
            if expression:
                return RoutedRequest(RequestRoute.MATH, expression)

        return RoutedRequest(RequestRoute.RAG, question)

    @staticmethod
    def _looks_like_equation(question: str) -> bool:
        return "=" in question or bool(re.search(r"\bx\s*\^?\s*\d", question, re.IGNORECASE))

    @staticmethod
    def _extract_equation(question: str) -> str:
        match = re.search(r"([0-9xXyY+*\-/().,^\s]+=[0-9xXyY+*\-/().,^\s]+)", question)
        if not match:
            return ""
        return match.group(1).strip().rstrip(" .,;:")

    @staticmethod
    def _extract_function_expression(question: str) -> str:
        match = re.search(
            r"funkcj[aeęi]\s+(?:f\s*\([^)]*\)\s*=\s*|y\s*=\s*)?(.+)$",
            question,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r"wykres\s+(?:f\s*\([^)]*\)\s*=\s*|y\s*=\s*)?(.+)$",
                question,
                re.IGNORECASE,
            )
        if not match:
            return ""
        expression = match.group(1).strip().rstrip("?.!")
        return re.sub(r"^y\s*=\s*", "", expression, flags=re.IGNORECASE)
