"""load_spec("package.module:ATTR") — same ergonomics as umwelt.spec."""
from __future__ import annotations

import importlib

from .types import WorldSpec


def load_spec(ref: str) -> WorldSpec:
    if ":" not in ref:
        raise ValueError(f"spec ref must be 'module:ATTR', got {ref!r}")
    module_name, attr = ref.split(":", 1)
    module = importlib.import_module(module_name)
    try:
        spec = getattr(module, attr)
    except AttributeError as e:
        raise ValueError(f"{module_name} has no attribute {attr!r}") from e
    if not isinstance(spec, WorldSpec):
        raise TypeError(f"{ref} is {type(spec).__name__}, not WorldSpec")
    return spec
