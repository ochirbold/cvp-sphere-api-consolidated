"""Compatibility shim. Canonical implementation moved to formula/ast/parser.py."""
try:
    from formula.ast.parser import *  # type: ignore
except ImportError:
    import importlib.util
    from pathlib import Path

    _target = Path(__file__).parent / "ast" / "parser.py"
    _spec = importlib.util.spec_from_file_location("_ast_parser_shim", _target)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("_")})
