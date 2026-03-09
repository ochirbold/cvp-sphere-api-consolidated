"""Compatibility shim. Canonical implementation moved to formula/core/runtime.py."""
try:
    from formula.core.runtime import *  # type: ignore
except ImportError:
    from core.runtime import *  # type: ignore
