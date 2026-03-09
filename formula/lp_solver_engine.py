"""Compatibility shim. Canonical implementation moved to formula/lp/solver.py."""
try:
    from formula.lp.solver import *  # type: ignore
except ImportError:
    from lp.solver import *  # type: ignore
