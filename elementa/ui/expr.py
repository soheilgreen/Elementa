
from __future__ import annotations
import ast, math

ALLOWED = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}

class SafeEvalError(Exception): pass

def safe_eval(expr, vars: dict[str, float] | None) -> float:
    if isinstance(expr, (int, float)): return float(expr)
    if expr is None: raise SafeEvalError("None expression")
    s = str(expr).strip()
    if s == "": raise SafeEvalError("Empty expression")
    node = ast.parse(s, mode="eval")

    def check(n):
        from ast import Expression, Constant, Num, BinOp, Add, Sub, Mult, Div, FloorDiv, Mod, Pow, UnaryOp, UAdd, USub, Name, Call
        if isinstance(n, ast.Expression): return check(n.body)
        if isinstance(n, (ast.Constant, ast.Num)):
            v = getattr(n, "n", getattr(n, "value", None))
            if isinstance(v, (int, float)): return
            raise SafeEvalError("Only numeric constants allowed")
        if isinstance(n, ast.BinOp) and isinstance(n.op, (Add, Sub, Mult, Div, FloorDiv, Mod, Pow)):
            check(n.left); check(n.right); return
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (UAdd, USub)):
            check(n.operand); return
        if isinstance(n, ast.Name):
            if n.id in (vars or {}) or n.id in ALLOWED: return
            raise SafeEvalError(f"Unknown name '{n.id}'")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ALLOWED:
            for a in n.args: check(a)
            return
        raise SafeEvalError(f"Unsupported syntax: {type(n).__name__}")
    check(node)
    env = dict(ALLOWED); env.update(vars or {})
    return float(eval(compile(node, "<expr>", "eval"), {"__builtins__": {}}, env))
