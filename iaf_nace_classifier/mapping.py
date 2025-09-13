import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON = REPO_ROOT / "sectores_iaf_completos.json"


def load_mapping(path: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    """Load IAF–NACE mapping JSON.

    If path is None, loads from `sectores_iaf_completos.json` at repo root.
    Filters out obviously broken records (e.g., missing codigos_nace).
    """
    p = Path(path) if path else DEFAULT_JSON
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned: List[Dict[str, Any]] = []
    for rec in data:
        codigos = [c.strip() for c in rec.get("codigos_nace", []) if str(c).strip()]
        if not codigos:
            # Skip entries without usable NACE codes
            continue
        cleaned.append({
            "codigo_iaf": rec.get("codigo_iaf"),
            "nombre_iaf": rec.get("nombre_iaf"),
            "codigos_nace": codigos,
            "exclusiones": [str(e).strip() for e in rec.get("exclusiones", []) if str(e).strip()],
        })
    return cleaned


_NACE_CODE_RE = re.compile(r"^\d{2}(?:\.\d{1,2})?")


def _normalize_nace(code: str) -> str:
    code = (code or "").strip()
    # Keep only the leading NACE pattern (e.g., 24, 24.4, 24.46)
    m = _NACE_CODE_RE.match(code)
    return m.group(0) if m else code


def _is_excluded(code: str, exclusions: Iterable[str]) -> bool:
    code_norm = _normalize_nace(code)
    for ex in exclusions:
        ex_norm = _normalize_nace(ex)
        if code_norm.startswith(ex_norm):
            return True
    return False


def _match_specificity(nace: str, pattern: str) -> Optional[int]:
    """Return specificity score if `nace` matches `pattern`, else None.

    Higher score means more specific match. Use pattern length as proxy.
    Matching rules:
    - If pattern has dot (e.g., 74.3), match by prefix (e.g., 74.31 matches 74.3)
    - If pattern is 2 digits (e.g., 24), match by major section prefix
    """
    n = _normalize_nace(nace)
    p = _normalize_nace(pattern)
    if not p:
        return None
    if n.startswith(p):
        return len(p)
    # Also allow 2-digit pattern to match 2-digit nace even if not dotted
    if len(p) == 2 and n[:2] == p:
        return 2
    return None


def classify_nace(code: str, mapping: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Classify a NACE code into an IAF sector.

    Returns a dict with keys: codigo_iaf, nombre_iaf, matched_pattern
    or None if no match.
    """
    if mapping is None:
        mapping = load_mapping()

    code_norm = _normalize_nace(code)
    best: Tuple[int, Dict[str, Any], str] | None = None  # (score, record, pattern)

    for rec in mapping:
        if _is_excluded(code_norm, rec.get("exclusiones", [])):
            continue
        for pat in rec.get("codigos_nace", []):
            score = _match_specificity(code_norm, pat)
            if score is None:
                continue
            if best is None or score > best[0]:
                best = (score, rec, _normalize_nace(pat))

    if not best:
        return None

    _, rec, pat = best
    return {
        "codigo_iaf": rec.get("codigo_iaf"),
        "nombre_iaf": rec.get("nombre_iaf"),
        "matched_pattern": pat,
        "nace_code": code_norm,
    }

