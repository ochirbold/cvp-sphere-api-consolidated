"""Compatibility shim. Canonical implementation moved to formula/lp/builder.py."""
try:
    from formula.lp.builder import *  # type: ignore
except ImportError:
    from lp.builder import *  # type: ignore
