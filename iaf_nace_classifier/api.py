"""
Servicio HTTP para clasificar códigos NACE → IAF.

Dependencias:
  pip install fastapi uvicorn

Ejecutar:
  uvicorn iaf_nace_classifier.api:app --reload

Endpoints:
  - GET /health
  - GET /classify?code=24.46
  - POST /classify  body: {"code": "24.46"} OR {"query": "..."}
  - GET /search?q=...
"""

from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from iaf_nace_classifier.search import buscar_actividad
from iaf_nace_classifier.mapping import load_mapping, classify_nace

app = FastAPI(title="IAF/NACE Classifier API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar mapeo globalmente
MAPPING = load_mapping()

# Servir archivos estáticos (frontend)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path), html=True), name="static")

@app.get("/")
async def read_index():
    if (static_path / "index.html").exists():
        return FileResponse(str(static_path / "index.html"))
    return {"message": "Frontend not found"}

@app.get("/health")
def health():
    return {"status": "ok", "sectors": len(MAPPING)}

# Modelo unificado para soportar ambos casos de uso en POST /classify
class UnifiedRequest(BaseModel):
    # Caso 1: Clasificación por código (Legacy)
    code: Optional[str] = None
    
    # Caso 2: Búsqueda avanzada (Nuevo)
    query: Optional[str] = None
    actividades_reales: Optional[str] = ""
    procesos_criticos: Optional[str] = ""

def _get_sector(mapping, codigo_iaf: Optional[int]) -> Optional[Dict[str, Any]]:
    if codigo_iaf is None:
        return None
    for s in mapping:
        if s.get("codigo_iaf") == codigo_iaf:
            return s
    return None

@app.get("/classify")
def classify_get(code: str = Query(..., description="Código NACE, p. ej. 24.46 o 47")):
    """Clasificar un código NACE específico (GET)."""
    res = classify_nace(code, MAPPING)
    if not res:
        raise HTTPException(status_code=404, detail="No match found")
    sector = _get_sector(MAPPING, res.get("codigo_iaf"))
    return {"input": code, "result": res, "sector": sector}

@app.post("/classify")
def classify_post(body: UnifiedRequest):
    """
    Endpoint unificado para clasificación.
    
    1. Si se proporciona 'code': Clasifica el código NACE (Legacy).
    2. Si se proporciona 'query': Realiza búsqueda avanzada por descripción/actividad.
    """
    # Caso 1: Clasificación por código
    if body.code:
        res = classify_nace(body.code, MAPPING)
        if not res:
            raise HTTPException(status_code=404, detail="No match found")
        sector = _get_sector(MAPPING, res.get("codigo_iaf"))
        return {"input": body.code, "result": res, "sector": sector}
    
    # Caso 2: Búsqueda avanzada
    if body.query:
        return buscar_actividad(
            query=body.query,
            actividades_reales=body.actividades_reales,
            procesos_criticos=body.procesos_criticos,
            mapping=MAPPING
        )
        
    raise HTTPException(status_code=400, detail="Must provide either 'code' or 'query'")

@app.get("/search")
def search(q: str = Query(..., min_length=2, description="Texto a buscar")):
    """Busca códigos NACE por descripción de actividad (GET)."""
    response = buscar_actividad(q, mapping=MAPPING, top_n=20)
    return {
        "query": q,
        "results": response['results'],
        "excluded": response['excluded']
    }
