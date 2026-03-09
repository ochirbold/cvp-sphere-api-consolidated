"""Compatibility shim. Canonical implementation moved to formula/dsl/parser.py."""
try:
    from formula.dsl.parser import *  # type: ignore
except ImportError:
    from dsl.parser import *  # type: ignore
