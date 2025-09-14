"""
Servicio HTTP para clasificar códigos NACE → IAF.

Dependencias:
  pip install fastapi uvicorn

Ejecutar:
  uvicorn api_server:app --reload

Endpoints:
  - GET /health
  - GET /classify?code=24.46
  - POST /classify  body: {"code": "24.46"}
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from iaf_nace_classifier import load_mapping, classify_nace


app = FastAPI(title="IAF–NACE Classifier API", version="0.1.0")


class ClassifyRequest(BaseModel):
    code: str


def _get_sector(mapping, codigo_iaf: Optional[int]) -> Optional[Dict[str, Any]]:
    if codigo_iaf is None:
        return None
    for s in mapping:
        if s.get("codigo_iaf") == codigo_iaf:
            return s
    return None


MAPPING = load_mapping()


@app.get("/health")
def health():
    return {"status": "ok", "sectors": len(MAPPING)}


@app.get("/classify")
def classify_get(code: str = Query(..., description="Código NACE, p. ej. 24.46 o 47")):
    res = classify_nace(code, MAPPING)
    if not res:
        raise HTTPException(status_code=404, detail="No match found")
    sector = _get_sector(MAPPING, res.get("codigo_iaf"))
    return {"input": code, "result": res, "sector": sector}


@app.post("/classify")
def classify_post(body: ClassifyRequest):
    res = classify_nace(body.code, MAPPING)
    if not res:
        raise HTTPException(status_code=404, detail="No match found")
    sector = _get_sector(MAPPING, res.get("codigo_iaf"))
    return {"input": body.code, "result": res, "sector": sector}

