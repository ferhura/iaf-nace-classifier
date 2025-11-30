import importlib.resources
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def load_mapping(path: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    """Load IAF–NACE mapping JSON.

    If path is None, loads from `iaf_nace_mapeo_expandido.json` packaged with the library.
    Filters out obviously broken records (e.g., missing codigos_nace).
    """
    if path:
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        ref = importlib.resources.files("iaf_nace_classifier") / "data" / "iaf_nace_mapeo_expandido.json"
        with ref.open("r", encoding="utf-8") as f:
            data = json.load(f)

    cleaned: List[Dict[str, Any]] = []
    
    # First pass: Collect all NACE descriptions for lookup
    nace_lookup: Dict[str, str] = {}
    for rec in data:
        for nace_item in rec.get("descripcion_nace", []):
            code = nace_item.get("codigo", "").strip()
            desc = nace_item.get("descripcion", "")
            if code:
                nace_lookup[code] = desc

    # Helper to extract exclusions
    def _extract_exclusions(text: str) -> str:
        text_lower = text.lower()
        exclusions = []
        if "excepto" in text_lower:
            parts = text.split("excepto", 1)
            if len(parts) > 1:
                exclusions.append("excepto " + parts[1])
        if "esta clase no comprende" in text_lower:
            parts = text.split("esta clase no comprende", 1)
            if len(parts) > 1:
                exclusions.append("esta clase no comprende " + parts[1])
        return " ".join(exclusions)

    # Helper to get parent code (e.g., 16.2 -> 16, 16.21 -> 16.2)
    def _get_parent_code(code: str) -> Optional[str]:
        if "." in code:
            parts = code.rsplit(".", 1)
            return parts[0]
        return None

    # Second pass: Build cleaned list and propagate exclusions
    for rec in data:
        codigos = [c.strip() for c in rec.get("codigos_nace", []) if str(c).strip()]
        if not codigos:
            continue
            
        # Process descriptions to add inherited exclusions
        processed_descriptions = []
        for nace_item in rec.get("descripcion_nace", []):
            code = nace_item.get("codigo", "").strip()
            desc = nace_item.get("descripcion", "")
            
            # Propagate from parent
            parent = _get_parent_code(code)
            while parent:
                if parent in nace_lookup:
                    parent_exclusions = _extract_exclusions(nace_lookup[parent])
                    if parent_exclusions:
                        # Append inherited exclusions to description so search.py picks them up
                        desc += f"\n{parent_exclusions}"
                    
                parent = _get_parent_code(parent)
            
            processed_descriptions.append({
                "codigo": code,
                "descripcion": desc
            })

        cleaned.append({
            "codigo_iaf": rec.get("codigo_iaf"),
            "nombre_iaf": rec.get("nombre_iaf"),
            "codigos_nace": codigos,
            "exclusiones": [str(e).strip() for e in rec.get("exclusiones", []) if str(e).strip()],
            "descripcion_nace": processed_descriptions,
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
