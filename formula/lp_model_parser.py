"""Compatibility shim. Canonical implementation moved to formula/lp/parser.py."""
try:
    from formula.lp.parser import *  # type: ignore
except ImportError:
    from lp.parser import *  # type: ignore
