# Repository Guidelines

## Project Structure & Module Organization
- `iaf_nace_classifier/`: core package.
  - `mapping.py`: `load_mapping`, `classify_nace` (pure functions, typed).
  - `cli.py`: CLI entry (`python -m iaf_nace_classifier.cli`).
- Root scripts: `api_server.py` (FastAPI API), `extract_iaf_nace.py` (PDF → JSON), `buscar_actividad.py` (búsqueda inversa), `ejemplo_busqueda.py`.
- Data: `iaf_nace_mapeo_expandido.json` (principal), `Codigo_NACE_sectoresema.pdf` (fuente).
- Docs: `README.md`, `GUIA_BUSQUEDA.md`. No carpeta `tests/` aún.

## Build, Test, and Development Commands
- CLI (clasificar): `python -m iaf_nace_classifier.cli 24.46 [--json] [-m path]`.
- API local: `pip install fastapi uvicorn pydantic` → `uvicorn api_server:app --reload`.
- Búsqueda inversa: `python buscar_actividad.py "restaurante" --top 5 --json`.
- Regenerar JSON: `pip install PyMuPDF` → `python extract_iaf_nace.py` (genera `iaf_nace_mapeo_expandido.json` y `extract_log.txt`).

## Coding Style & Naming Conventions
- Python 3.10+, PEP 8, indentación 4 espacios, UTF-8 explícito al leer/escribir.
- Nombres: `snake_case` para funciones/módulos, `CapWords` para clases, `SCREAMING_SNAKE_CASE` para constantes.
- Tipado: usa anotaciones y `Optional`, `List`, etc. Mantén funciones pequeñas y puras en `mapping.py`.
- Estructura de paths: usa `pathlib.Path` relativo al repo (ver `REPO_ROOT`).

## Testing Guidelines
- Framework sugerido: `pytest`. Estructura: `tests/` con archivos `test_*.py`.
- Mínimos a cubrir: normalización de NACE, exclusiones, “match más específico”, y casos sin match.
- Ejecutar: `pytest -q`. Si añades fixtures grandes, coloca datos en `tests/data/`.

## Commit & Pull Request Guidelines
- Commits pequeños, en imperativo (ES o EN), p. ej.: `feat(cli): soporta salida JSON` o `Corrige exclusiones 24.4`.
- Describe el “por qué” y ejemplos de uso (comandos/entradas/salida). En PRs incluye:
  - Resumen, cambios principales, issue vinculado.
  - Ejemplos reproducibles: `python -m iaf_nace_classifier.cli 47 --json` y, si aplica, `curl` al API.
  - Actualiza `README.md`/`GUIA_BUSQUEDA.md` si cambia el comportamiento.

## Security & Configuration Tips
- No subas entornos `venv/` ni artefactos temporales; respeta `.gitignore`.
- El JSON es grande: evita duplicados y confirma que el extractor actualiza solo lo necesario.
- Cambios de esquema en el JSON deben documentarse y mantenerse retrocompatibles cuando sea posible.

## Agent-Specific Notes
- Mantén estables `load_mapping` y `classify_nace`; si cambian firmas o claves de retorno, sincroniza CLI, API y ejemplos.
- Al tocar reglas de matching, añade casos en `tests/` y referencia `extract_log.txt` para validar cobertura.
