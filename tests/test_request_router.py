from src.services.request_router import RequestRoute, RequestRouter


def test_router_sends_natural_equation_to_math_service():
    routed = RequestRouter().route("Rozwiąż równanie x^2 - 4 = 0")

    assert routed.route == RequestRoute.MATH
    assert routed.payload == "x^2 - 4 = 0"


def test_router_removes_sentence_punctuation_from_equation():
    routed = RequestRouter().route(
        "To teraz rozwiąż równanie x^2 -2x + 1 = 0, również za pomocą delty"
    )

    assert routed.route == RequestRoute.MATH
    assert routed.payload == "x^2 -2x + 1 = 0"


def test_router_sends_natural_circle_request_to_plot_service():
    routed = RequestRouter().route("Narysuj okrąg ze środkiem i promieniem")

    assert routed.route == RequestRoute.PLOT
    assert routed.plot_type == "circle"


def test_router_keeps_general_question_in_rag():
    routed = RequestRouter().route("Jak CKE ocenia dowód z geometrii?")

    assert routed.route == RequestRoute.RAG


def test_router_keeps_explicit_plot_compatibility():
    routed = RequestRouter().route("wykres 2d: sin(x)")

    assert routed.route == RequestRoute.PLOT
    assert routed.plot_type == "2d"
    assert routed.payload == "sin(x)"


def test_router_extracts_natural_function_expression():
    routed = RequestRouter().route("Narysuj wykres funkcji y = x^2 + y^2")

    assert routed.route == RequestRoute.PLOT
    assert routed.plot_type == "3d"
    assert routed.payload == "x^2 + y^2"