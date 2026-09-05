from __future__ import annotations

import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
_X, _Y = sp.symbols("x y")
_ALLOWED_LOCALS = {
    "x": _X,
    "y": _Y,
    "pi": sp.pi,
    "E": sp.E,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sqrt": sp.sqrt,
    "log": sp.log,
    "exp": sp.exp,
    "abs": sp.Abs,
}


class MathService:
    # TODO: Keep this service as a deterministic calculation/verification layer.
    # A future math agent should select methods and produce a generic structured
    # solution response; MathService should return typed artifacts and checks,
    # not the final pedagogical prose shown to the user.

    def parse_expression(self, expression: str, dimensions: int = 1) -> sp.Expr:
        allowed_symbols = {"x"} if dimensions == 1 else {"x", "y"}
        cleaned = expression.strip().replace("^", "**")
        if not re.fullmatch(r"[0-9a-zA-Z_+*\-/().,\s]+", cleaned):
            raise ValueError("Wyrażenie zawiera niedozwolone znaki.")
        parsed = parse_expr(
            cleaned,
            local_dict={key: value for key, value in _ALLOWED_LOCALS.items() if key in allowed_symbols or key in {"pi", "E", "sin", "cos", "tan", "sqrt", "log", "exp", "abs"}},
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
        if not isinstance(parsed, sp.Expr):
            raise ValueError("Nie udało się odczytać pojedynczego wyrażenia matematycznego.")
        unknown_symbols = parsed.free_symbols - {
            _X,
            _Y,
        }
        if unknown_symbols or (dimensions == 1 and _Y in parsed.free_symbols):
            raise ValueError("Dozwolone są tylko zmienne x oraz y dla wykresu 3D.")
        return parsed

    def solve(self, expression: str) -> list[sp.Expr]:
        if "=" in expression:
            left, right = expression.split("=", 1)
            equation = self.parse_expression(left) - self.parse_expression(right)
        else:
            equation = self.parse_expression(expression)
        return sp.solve(equation, _X)

    def format_solution(self, expression: str) -> str:
        solutions = self.solve(expression)
        if not solutions:
            return "Nie znalazłem rozwiązania w dziedzinie symbolicznej."
        return "Rozwiązania: " + ", ".join(f"${sp.latex(solution)}$" for solution in solutions)

    @staticmethod
    def extract_tool_request(question: str) -> tuple[str, str] | None:
        match = re.match(r"^\s*(wykres|plot)\s*(2d|3d)?\s*:\s*(.+?)\s*$", question, re.IGNORECASE)
        if match:
            dimensions = match.group(2) or "2d"
            return dimensions.lower(), match.group(3)
        if re.search(r"\b(narysuj|rysuj|wykre[sś]l)\b", question, re.IGNORECASE) and re.search(
            r"\b(okr[ąa]g|ko[łl]o)\b", question, re.IGNORECASE
        ):
            return "circle", "unit"
        return None

    @staticmethod
    def is_solve_request(question: str) -> bool:
        return bool(re.match(r"^\s*(rozwiąż|solve)\s*:\s*.+", question, re.IGNORECASE))

    @staticmethod
    def extract_solve_expression(question: str) -> str:
        return re.sub(r"^\s*(rozwiąż|solve)\s*:\s*", "", question, flags=re.IGNORECASE)
