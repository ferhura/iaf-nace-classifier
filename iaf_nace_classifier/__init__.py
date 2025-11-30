"""
IAF–NACE classifier utilities.

Primary entrypoints:
- classify_nace(code): returns matching IAF sector for a NACE code
- load_mapping(path=None): loads mapping from JSON (defaults to repo file)
- buscar_actividad(query): searches NACE codes by activity description
"""

from .mapping import load_mapping, classify_nace
from .search import buscar_actividad

__all__ = ["load_mapping", "classify_nace", "buscar_actividad"]

