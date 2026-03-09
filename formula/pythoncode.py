"""Compatibility shim. Canonical implementation moved to formula/core/orchestrator.py."""
try:
    from formula.core.orchestrator import *  # type: ignore
    from formula.core.orchestrator import main  # type: ignore
except ImportError:
    from core.orchestrator import *  # type: ignore
    from core.orchestrator import main  # type: ignore

if __name__ == "__main__":
    main()
