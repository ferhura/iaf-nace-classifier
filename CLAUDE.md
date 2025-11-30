# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IAF-NACE Classifier maps EU NACE codes to IAF sectors with full hierarchical NACE descriptions. The system consists of:
- PDF extraction pipeline that parses `data/Codigo_NACE_sectoresema.pdf` to generate structured mappings
- Classification API that matches NACE codes to IAF sectors with prefix matching and exclusion rules
- Reverse search functionality to find NACE codes from activity descriptions
- CLI, HTTP API, and Python library interfaces

## Project Structure

```
iaf-nace-classifier/
├── iaf_nace_classifier/      # Main package
│   ├── __init__.py           # Public API exports
│   ├── mapping.py            # NACE → IAF classification
│   ├── search.py             # Activity → NACE reverse search
│   ├── cli.py                # Classification CLI
│   └── api.py                # FastAPI HTTP server
├── data/                     # Data files
│   ├── Codigo_NACE_sectoresema.pdf
│   └── iaf_nace_mapeo_expandido.json
├── scripts/                  # Utilities
│   ├── extract_iaf_nace.py   # PDF extractor
│   └── buscar_actividad.py   # Search CLI
├── examples/                 # Usage examples
│   └── ejemplo_busqueda.py
├── docs/                     # Documentation
│   └── GUIA_BUSQUEDA.md
└── pyproject.toml            # Package configuration
```

## Core Architecture

### Data Flow

1. **Extraction** (`scripts/extract_iaf_nace.py`): Parses PDF → produces `data/iaf_nace_mapeo_expandido.json`
2. **Classification** (`iaf_nace_classifier/mapping.py`): Loads JSON → applies matching rules → returns IAF sector
3. **Reverse Search** (`iaf_nace_classifier/search.py`): Activity description → searches NACE descriptions → returns matches
4. **Interfaces**: CLI (`cli.py`), Search CLI (`scripts/buscar_actividad.py`), and HTTP API (`api.py`)

### Key Components

**Classifier Module** (`iaf_nace_classifier/mapping.py`)
- `load_mapping()`: Loads and validates JSON from `data/iaf_nace_mapeo_expandido.json`, filters invalid records
- `classify_nace()`: Implements specificity-based matching (longer prefix wins)
- `_is_excluded()` (line 47): Respects sector exclusions
- `_match_specificity()` (line 56): Calculates match score based on prefix length

**Search Module** (`iaf_nace_classifier/search.py`)
- `buscar_actividad()`: Main search function, returns ranked results
- `calcular_relevancia()`: Scores text similarity using keyword matching and phrase detection
- `normalizar_texto()`: Removes accents and normalizes text for comparison

**PDF Extractor** (`scripts/extract_iaf_nace.py`)
- Page 1: Table extraction via Y-coordinate clustering and column alignment
- Pages 2-N: NACE descriptions via header detection (`NN`, `NN.N`, `NN.NN` patterns)
- Hierarchical expansion: `01` expands to all `01.*` subcodes unless excluded
- OCR normalization: Corrects common errors like `except0` → `excepto`
- Outputs to `data/` directory and `extract_log.txt` in root

**HTTP API** (`iaf_nace_classifier/api.py`)
- FastAPI server with GET/POST `/classify` endpoints
- Returns both classification result and full sector object with NACE descriptions
- Preloads mapping at startup for performance

### Data Format

`data/iaf_nace_mapeo_expandido.json` structure:
```json
{
  "codigo_iaf": int,
  "nombre_iaf": str,
  "codigos_nace": ["24", "24.46"],  // Base patterns
  "exclusiones": ["24.4"],          // Excluded prefixes
  "descripcion_nace": [             // Expanded hierarchy
    {"codigo": "24", "descripcion": "..."},
    {"codigo": "24.46", "descripcion": "..."}
  ]
}
```

### Classification Rules

1. **Prefix matching**: Input `24.46` matches patterns `24` and `24.46`
2. **Specificity wins**: Longer matching prefix takes precedence
3. **Exclusions respected**: Skip sectors that explicitly exclude the prefix
4. **Normalization**: Accepts `"24"`, `"24.46"`, etc., normalizes via regex `^\d{2}(?:\.\d{1,2})?`

### Reverse Search Algorithm

Calculates relevance score based on:
- Exact phrase match: +100 points
- Individual keywords: +5 to +10 points (word boundary bonus)
- Keyword density: +0 to +20 points
- Spanish stopwords filtered out
- Results sorted by relevance (descending)

## Common Commands

### Installation
```bash
# Basic installation (classification only)
pip install -e .

# With API dependencies
pip install -e ".[api]"

# With PDF extractor
pip install -e ".[extractor]"

# Full development setup
pip install -e ".[api,extractor,dev]"
```

### Run Classification (CLI)
```bash
# Classify a NACE code
python -m iaf_nace_classifier.cli 24.46

# JSON output
python -m iaf_nace_classifier.cli 47 --json

# Use custom mapping file
python -m iaf_nace_classifier.cli 74.31 -m data/iaf_nace_mapeo_expandido.json
```

### Run Reverse Search (CLI)
```bash
# Search by activity description
python scripts/buscar_actividad.py "fabricación de muebles" --top 5

# JSON output
python scripts/buscar_actividad.py "restaurante" --json

# Full descriptions
python scripts/buscar_actividad.py "software" --full
```

### Run HTTP API
```bash
# Install API dependencies
pip install -e ".[api]"

# Start server (note new module path)
uvicorn iaf_nace_classifier.api:app --reload

# Test endpoints
curl 'http://127.0.0.1:8000/health'
curl 'http://127.0.0.1:8000/classify?code=24.46'
curl -X POST 'http://127.0.0.1:8000/classify' -H 'Content-Type: application/json' -d '{"code":"47"}'
```

### Regenerate Data from PDF
```bash
# Install extractor dependencies
pip install -e ".[extractor]"

# Run extractor (note new script location)
python scripts/extract_iaf_nace.py

# Outputs:
# - data/iaf_nace_mapeo_expandido.json (mapping data)
# - extract_log.txt (validation metrics and warnings)
```

### Use as Python Library
```python
# Classification
from iaf_nace_classifier import load_mapping, classify_nace
mapping = load_mapping()
result = classify_nace("24.46", mapping)
# Returns: {"codigo_iaf": int, "nombre_iaf": str, "matched_pattern": str, "nace_code": str}

# Reverse search
from iaf_nace_classifier import buscar_actividad
resultados = buscar_actividad("desarrollo de software", top_n=5)
# Returns: [{"codigo_nace": str, "codigo_iaf": int, "nombre_iaf": str, "relevancia": float, ...}, ...]
```

## Development Notes

- **Python version**: Requires Python >= 3.10
- **No dependencies** for basic classifier/CLI (pure Python)
- **Virtual environment**: `venv/` directory present (standard Python venv)
- **Data location**: `iaf_nace_classifier/mapping.py:9` resolves to `REPO_ROOT/data/iaf_nace_mapeo_expandido.json`
- **Package installable**: Use `pip install -e .` to install in development mode

### PDF Extractor Tuning

If the PDF layout changes, adjust in `scripts/extract_iaf_nace.py`:
- `Y_TOL` (lines 87, 272): Vertical tolerance for line grouping
- `IAF_START_RE` (line 22): Regex for IAF sector headers
- `HEAD_RE` (line 253): Regex for NACE description headers
- Alignment thresholds (lines 181, 194): Y-distance for column matching
- Paths now point to `data/` directory (lines 9-12)

### Validation

After extraction, always review `extract_log.txt` in project root:
- Counts extracted sectors vs. expected
- Reports NACE codes without descriptions
- Lists warnings about suspicious names or missing codes
- Shows total expanded codes after hierarchy processing

## Code Patterns

### Adding New Classification Rules

Modify `iaf_nace_classifier/mapping.py`:
- `_match_specificity()` (line 56): Adjust matching logic
- `_is_excluded()` (line 47): Modify exclusion behavior
- `classify_nace()` (line 76): Change selection algorithm

### Extending the Search Algorithm

Modify `iaf_nace_classifier/search.py`:
- `calcular_relevancia()`: Adjust scoring weights
- `normalizar_texto()`: Add more accent/character replacements
- `buscar_actividad()`: Change result filtering or ranking

### Extending the API

`iaf_nace_classifier/api.py` uses FastAPI with Pydantic models:
- Add new endpoints to `app`
- Use `MAPPING` global (preloaded at startup for performance)
- Helper `_get_sector()` retrieves full sector by IAF code
- Import from package using relative imports: `from . import load_mapping, classify_nace`

### Adding Examples

Place example scripts in `examples/` directory:
- Add sys.path manipulation to import package: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`
- Import from package: `from iaf_nace_classifier import ...`
- See `examples/ejemplo_busqueda.py` for reference

## Important File Locations

- **Main package**: `iaf_nace_classifier/`
- **Data files**: `data/` (PDF and JSON)
- **Scripts**: `scripts/` (extractor and search CLI)
- **Examples**: `examples/`
- **Documentation**: `docs/` and README.md
- **Configuration**: `pyproject.toml` (package metadata and dependencies)
