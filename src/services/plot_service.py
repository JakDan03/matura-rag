from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from src.services.math_service import MathService


class PlotService:
    def __init__(self, math_service: MathService | None = None):
        self.math_service = math_service or MathService()

    def plot_2d(self, expression: str, minimum: float = -10, maximum: float = 10):
        parsed = self.math_service.parse_expression(expression, dimensions=1)
        x_values = np.linspace(minimum, maximum, 500)
        function = self._lambdify(parsed, ("x",))
        y_values = function(x_values)
        figure = go.Figure(go.Scatter(x=x_values, y=y_values, mode="lines", name=f"f(x) = {parsed}"))
        figure.update_layout(xaxis_title="x", yaxis_title="f(x)", template="plotly_white")
        return figure

    def plot_3d(
        self,
        expression: str,
        minimum: float = -5,
        maximum: float = 5,
        resolution: int = 100,
    ):
        parsed = self.math_service.parse_expression(expression, dimensions=2)
        x_values = np.linspace(minimum, maximum, resolution)
        y_values = np.linspace(minimum, maximum, resolution)
        x_grid, y_grid = np.meshgrid(x_values, y_values)
        function = self._lambdify(parsed, ("x", "y"))
        z_grid = function(x_grid, y_grid)
        figure = go.Figure(go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale="Viridis"))
        figure.update_layout(
            scene={"xaxis_title": "x", "yaxis_title": "y", "zaxis_title": "f(x, y)"},
            template="plotly_white",
        )
        return figure

    def plot_circle(self, radius: float = 1.0, center_x: float = 0.0, center_y: float = 0.0):
        angles = np.linspace(0, 2 * np.pi, 500)
        x_values = center_x + radius * np.cos(angles)
        y_values = center_y + radius * np.sin(angles)
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name="Okrąg",
                fill="toself",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[center_x],
                y=[center_y],
                mode="markers+text",
                text=["Środek O"],
                textposition="top center",
                name="Środek",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[center_x, center_x + radius],
                y=[center_y, center_y],
                mode="lines+text",
                text=[None, "r"],
                textposition="top center",
                name="Promień",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[center_x - radius, center_x + radius],
                y=[center_y, center_y],
                mode="lines+text",
                text=[None, "d"],
                textposition="bottom center",
                name="Średnica",
            )
        )
        figure.update_layout(
            xaxis={"title": "x", "scaleanchor": "y", "scaleratio": 1},
            yaxis_title="y",
            template="plotly_white",
        )
        return figure

    @staticmethod
    def _lambdify(expression, variables):
        import sympy as sp

        return sp.lambdify(variables, expression, modules=["numpy"])
