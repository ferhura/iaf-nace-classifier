"""
Servicio HTTP para clasificar códigos NACE → IAF.

Dependencias:
  pip install fastapi uvicorn

Ejecutar:
  uvicorn iaf_nace_classifier.api:app --reload

Endpoints:
  - GET /health
  - GET /classify?code=24.46
  - POST /classify  body: {"code": "24.46"}
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

from . import load_mapping, classify_nace
from .search import buscar_actividad


app = FastAPI(title="IAF–NACE Classifier API", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/search")
def search(q: str = Query(..., min_length=2, description="Texto a buscar")):
    """Busca códigos NACE por descripción de actividad."""
    response = buscar_actividad(q, mapping=MAPPING, top_n=20)
    return {
        "query": q,
        "results": response['results'],
        "excluded": response['excluded']
    }


# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


