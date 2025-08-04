"""PDF statement parsers."""
from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, Type

PARSER_REGISTRY: Dict[str, Type] = {}


def _load_parsers() -> Dict[str, Type]:
    registry: Dict[str, Type] = {}
    package = __name__
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{package}.{module_name}")
        parser_cls = getattr(module, "Parser", None)
        if parser_cls is None:
            continue
        name = getattr(module, "BANK", module_name)
        registry[name] = parser_cls
        globals()[parser_cls.__name__] = parser_cls
    return registry


PARSER_REGISTRY = _load_parsers()

__all__ = [cls.__name__ for cls in PARSER_REGISTRY.values()] + ["PARSER_REGISTRY"]
