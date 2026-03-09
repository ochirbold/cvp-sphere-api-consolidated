"""Compatibility shim. Canonical implementation moved to formula/dsl/extractor.py."""
try:
    from formula.dsl.extractor import *  # type: ignore
except ImportError:
    from dsl.extractor import *  # type: ignore
