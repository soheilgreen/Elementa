"""
Tests for elementa.core — parameter evaluator and exceptions.
"""

import pytest
from elementa.core.evaluator import ParameterEvaluator
from elementa.core.exceptions import ParameterEvaluationError
from elementa.ui.expr import safe_eval, SafeEvalError


# ---------------------------------------------------------------------------
# safe_eval
# ---------------------------------------------------------------------------

class TestSafeEval:
    def test_plain_number(self):
        assert safe_eval("3.14", {}) == pytest.approx(3.14)

    def test_arithmetic(self):
        assert safe_eval("2 + 3 * 4", {}) == pytest.approx(14.0)

    def test_power(self):
        assert safe_eval("2**10", {}) == pytest.approx(1024.0)

    def test_variable(self):
        assert safe_eval("W * 2", {"W": 5.0}) == pytest.approx(10.0)

    def test_math_function(self):
        import math
        assert safe_eval("sqrt(4)", {}) == pytest.approx(2.0)
        assert safe_eval("sin(pi/2)", {}) == pytest.approx(1.0)

    def test_unknown_variable_raises(self):
        with pytest.raises(SafeEvalError):
            safe_eval("unknown_var", {})

    def test_forbidden_builtin_raises(self):
        with pytest.raises(SafeEvalError):
            safe_eval("__import__('os')", {})

    def test_empty_raises(self):
        with pytest.raises(SafeEvalError):
            safe_eval("", {})


# ---------------------------------------------------------------------------
# ParameterEvaluator
# ---------------------------------------------------------------------------

class TestParameterEvaluator:
    def test_simple_resolve(self):
        result = ParameterEvaluator.resolve_parameters({"W": "0.1", "H": "0.05"})
        assert result["W"] == pytest.approx(0.1)
        assert result["H"] == pytest.approx(0.05)

    def test_dependency_resolution(self):
        result = ParameterEvaluator.resolve_parameters({
            "L": "2.0",
            "half_L": "L / 2",
        })
        assert result["half_L"] == pytest.approx(1.0)

    def test_chained_dependencies(self):
        result = ParameterEvaluator.resolve_parameters({
            "a": "1.0",
            "b": "a + 1",
            "c": "b * 2",
        })
        assert result["c"] == pytest.approx(4.0)

    def test_circular_dependency_raises(self):
        with pytest.raises(ParameterEvaluationError):
            ParameterEvaluator.resolve_parameters({
                "a": "b + 1",
                "b": "a + 1",
            })

    def test_evaluate_expression(self):
        val = ParameterEvaluator.evaluate_expression("W * H", {"W": 3.0, "H": 4.0})
        assert val == pytest.approx(12.0)

    def test_evaluate_points(self):
        pts = ParameterEvaluator.evaluate_points(
            "[(0, 0), (L, 0), (L/2, H)]",
            {"L": 2.0, "H": 1.0},
        )
        assert len(pts) == 3
        assert pts[0] == pytest.approx((0.0, 0.0))
        assert pts[1] == pytest.approx((2.0, 0.0))
        assert pts[2] == pytest.approx((1.0, 1.0))
