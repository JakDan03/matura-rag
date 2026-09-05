from src.services.plot_service import PlotService


def test_plot_2d_returns_plotly_figure():
    figure = PlotService().plot_2d("sin(x)")

    assert len(figure.data) == 1
    assert len(figure.data[0].x) == 500


def test_plot_3d_returns_surface_figure():
    figure = PlotService().plot_3d("x**2 + y**2", resolution=20)

    assert len(figure.data) == 1
    assert figure.data[0].type == "surface"
    assert len(figure.data[0].z) == 20


def test_plot_circle_contains_center_radius_and_diameter():
    figure = PlotService().plot_circle()

    assert len(figure.data) == 4
    assert {trace.name for trace in figure.data} == {
        "Okrąg",
        "Środek",
        "Promień",
        "Średnica",
    }
