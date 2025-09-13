"""
IAF–NACE classifier utilities.

Primary entrypoints:
- classify_nace(code): returns matching IAF sector for a NACE code
- load_mapping(path=None): loads mapping from JSON (defaults to repo file)
"""

from .mapping import load_mapping, classify_nace

__all__ = ["load_mapping", "classify_nace"]

