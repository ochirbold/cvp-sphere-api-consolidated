"""Compatibility shim. Canonical implementation moved to formula/utils/unicode.py."""
try:
    from formula.utils.unicode import *  # type: ignore
except ImportError:
    from utils.unicode import *  # type: ignore
