# Repository Guidelines

## Project Structure & Modules
- `iaf_nace_classifier/`: core package
  - `mapping.py`: `load_mapping`, `classify_nace` (puras, con tipos)
  - `search.py`: búsqueda inversa actividad → NACE/IAF
  - `cli.py`: CLI de clasificación (`python -m iaf_nace_classifier.cli`)
  - `api.py`: servidor FastAPI (`uvicorn iaf_nace_classifier.api:app --reload`)
- `data/`: `iaf_nace_mapeo_expandido.json`, `Codigo_NACE_sectoresema.pdf`
- `scripts/`: utilidades (`extract_iaf_nace.py`, `buscar_actividad.py`)
- `examples/`: ejemplos de uso
- `tests/`: pruebas con `pytest`
- `pyproject.toml`: packaging, extras y tooling (black/ruff/pytest)

## Build, Test, Dev Commands
- Instalar editable: `pip install -e .` (extras: `.[api]`, `.[extractor]`, `.[dev]`)
- CLI: `iaf-nace-classify 24.46 --json` o `python -m iaf_nace_classifier.cli 24.46`
- Búsqueda: `iaf-nace-search "restaurante" --top 5` o `python scripts/buscar_actividad.py ...`
- API: `uvicorn iaf_nace_classifier.api:app --reload`
- Regenerar JSON: `python scripts/extract_iaf_nace.py` (genera `data/iaf_nace_mapeo_expandido.json` y `extract_log.txt`)
- Tests: `pytest -q` (coverage: `pytest --cov=iaf_nace_classifier`)
- Lint/format: `ruff check .` y `black .`

## Coding Style & Naming
- Python ≥ 3.10, PEP 8, 4 espacios, UTF-8 explícito
- Nombres: `snake_case` (funciones/módulos), `CapWords` (clases), `SCREAMING_SNAKE_CASE` (constantes)
- Tipado obligatorio en API pública; longitud de línea 100 (configurada en `pyproject.toml`)
- Rutas con `pathlib.Path`; funciones puras y pequeñas en `mapping.py`

## Testing Guidelines
- Estructura: `tests/test_*.py`; datos de prueba en `tests/data/`
- Casos mínimos: normalización NACE, exclusiones, “match más específico”, sin match y ejemplos de búsqueda
- Ejecuta `pytest -q` localmente y asegura cobertura básica de `mapping.py`

## Commit & Pull Requests
- Mensajes en imperativo y concisos, ej.: `feat(cli): salida JSON` o `fix(mapping): exclusiones 24.4`
- En PR: descripción, “por qué”, pasos de reproducción (CLI/API), y cambios en docs si aplica
- Mantén retrocompatibilidad del JSON y de la API (`classify_nace` retorna: `codigo_iaf`, `nombre_iaf`, `matched_pattern`, `nace_code`)

## Security & Config
- No commitear `venv/` ni artefactos; respeta `.gitignore`
- Evita duplicar el JSON grande; documenta cambios de esquema y sincroniza consumidores
- Usa extras `.[api]` y `.[extractor]` para dependencias opcionales
