import sympy as sp
import pytest

from src.services.math_service import MathService


def test_solve_equation_returns_symbolic_solution():
    service = MathService()

    assert service.solve("x**2 = 4") == [-2, 2]
    assert service.format_solution("x**2 = 4") == "Rozwiązania: $-2$, $2$"


def test_plot_requests_are_detected():
    service = MathService()

    assert service.extract_tool_request("wykres 2d: sin(x)") == ("2d", "sin(x)")
    assert service.extract_tool_request("plot 3D: x^2 + y^2") == ("3d", "x^2 + y^2")
    assert service.extract_tool_request("Jak policzyć pole koła?") is None


def test_circle_request_is_detected_without_expression_syntax():
    assert MathService.extract_tool_request(
        "Narysuj mi okrąg. Zaznacz na nim środek, promień oraz średnicę"
    ) == ("circle", "unit")


def test_unsupported_expression_is_rejected():
    service = MathService()

    with pytest.raises(ValueError):
        service.parse_expression("__import__('os').system('dir')")


def test_expression_is_sympy_expression():
    assert isinstance(MathService().parse_expression("2x + 1"), sp.Expr)
