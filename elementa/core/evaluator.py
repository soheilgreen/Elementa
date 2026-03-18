from typing import Dict

from .logger import get_logger
from .exceptions import ParameterEvaluationError

from ..ui.expr import safe_eval, SafeEvalError

logger = get_logger(__name__)

class ParameterEvaluator:
    """Evaluates mathematical expressions and resolves dependencies between parameters."""
    
    @staticmethod
    def evaluate_expression(expr_str: str, available_params: Dict[str, float]) -> float:
        """Evaluates a single expression string using the available parameters."""
        try:
            return safe_eval(expr_str, available_params)
        except Exception as e:
            logger.error(f"Expression error: '{expr_str}' -> {e}")
            raise ParameterEvaluationError(f"Error evaluating '{expr_str}': {e}") from e

    @staticmethod
    def evaluate_points(expr_str: str, available_params: Dict[str, float]) -> list:
        """Evaluates a string representing a list of tuples, e.g. '[(0, 0), (dx, 0)]'."""
        import ast
        try:
            node = ast.parse(expr_str, mode='eval')
            if not isinstance(node.body, ast.List):
                raise ValueError("Expected a list")
            points = []
            for elt in node.body.elts:
                if not isinstance(elt, ast.Tuple) or len(elt.elts) != 2:
                    raise ValueError("Expected a list of 2-tuples")
                x_str = ast.unparse(elt.elts[0])
                y_str = ast.unparse(elt.elts[1])
                x = ParameterEvaluator.evaluate_expression(x_str, available_params)
                y = ParameterEvaluator.evaluate_expression(y_str, available_params)
                points.append((x, y))
            return points
        except Exception as e:
            logger.error(f"Points evaluation error: '{expr_str}' -> {e}")
            raise ParameterEvaluationError(f"Error evaluating points '{expr_str}': {e}") from e

    @staticmethod
    def resolve_parameters(raw_parameters: Dict[str, str]) -> Dict[str, float]:
        """Resolves a dictionary of raw string parameters into a dictionary of float values."""
        eval_params = {}
        # Iterate to resolve dependencies
        for _ in range(len(raw_parameters) + 1):
            for name, expr in raw_parameters.items():
                if name not in eval_params:
                    try:
                        eval_params[name] = safe_eval(expr, eval_params)
                    except (SafeEvalError, NameError):
                        continue
        
        if len(eval_params) != len(raw_parameters):
            unresolved = set(raw_parameters.keys()) - set(eval_params.keys())
            msg = f"Could not resolve parameters: {unresolved}. Check for circular dependencies or invalid syntax."
            logger.error(msg)
            raise ParameterEvaluationError(msg)
            
        return eval_params
