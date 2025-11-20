# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IAF-NACE Classifier maps EU NACE codes to IAF sectors with full hierarchical NACE descriptions. The system consists of:
- PDF extraction pipeline that parses `Codigo_NACE_sectoresema.pdf` to generate structured mappings
- Classification API that matches NACE codes to IAF sectors with prefix matching and exclusion rules
- CLI and HTTP API interfaces for code classification

## Core Architecture

### Data Flow
1. **Extraction** (`extract_iaf_nace.py`): Parses PDF → produces `iaf_nace_mapeo_expandido.json`
2. **Classification** (`iaf_nace_classifier/mapping.py`): Loads JSON → applies matching rules → returns IAF sector
3. **Interfaces**: CLI (`cli.py`) and HTTP API (`api_server.py`) expose classification functionality

### Key Components

**Classifier Module** (`iaf_nace_classifier/`)
- `mapping.py`: Core classification logic with prefix matching and exclusion rules
  - `load_mapping()`: Loads and validates JSON, filters invalid records
  - `classify_nace()`: Implements specificity-based matching (longer prefix wins)
  - `_is_excluded()`: Respects sector exclusions
- `cli.py`: Command-line interface with JSON/text output modes
- `__init__.py`: Public API exports

**PDF Extractor** (`extract_iaf_nace.py`)
- Page 1: Table extraction via Y-coordinate clustering and column alignment
- Pages 2-N: NACE descriptions via header detection (`NN`, `NN.N`, `NN.NN` patterns)
- Hierarchical expansion: `01` expands to all `01.*` subcodes unless excluded
- OCR normalization: Corrects common errors like `except0` → `excepto`

**HTTP API** (`api_server.py`)
- FastAPI server with GET/POST `/classify` endpoints
- Returns both classification result and full sector object with NACE descriptions

### Data Format

`iaf_nace_mapeo_expandido.json` structure:
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

## Common Commands

### Run Classification (CLI)
```bash
# Classify a NACE code
python -m iaf_nace_classifier.cli 24.46

# JSON output
python -m iaf_nace_classifier.cli 47 --json

# Use custom mapping file
python -m iaf_nace_classifier.cli 74.31 -m iaf_nace_mapeo_expandido.json
```

### Run HTTP API
```bash
# Install optional dependencies
pip install fastapi uvicorn

# Start server
uvicorn api_server:app --reload

# Test endpoints
curl 'http://127.0.0.1:8000/classify?code=24.46'
curl -X POST 'http://127.0.0.1:8000/classify' -H 'Content-Type: application/json' -d '{"code":"47"}'
```

### Regenerate Data from PDF
```bash
# Install PyMuPDF
pip install PyMuPDF

# Run extractor
python extract_iaf_nace.py

# Outputs:
# - iaf_nace_mapeo_expandido.json (mapping data)
# - extract_log.txt (validation metrics and warnings)
```

### Use as Python Library
```bash
# Install in editable mode
pip install -e .

# Use in code
from iaf_nace_classifier import load_mapping, classify_nace
mapping = load_mapping()
result = classify_nace("24.46", mapping)
# Returns: {"codigo_iaf": int, "nombre_iaf": str, "matched_pattern": str, "nace_code": str}
```

## Development Notes

- **Python version**: Requires Python >= 3.10
- **No dependencies** for classifier/CLI (pure Python)
- **Virtual environment**: `venv/` directory present (standard Python venv)
- **JSON file location**: `iaf_nace_classifier/mapping.py:7-9` resolves to `REPO_ROOT/iaf_nace_mapeo_expandido.json`

### PDF Extractor Tuning

If the PDF layout changes, adjust in `extract_iaf_nace.py`:
- `Y_TOL` (line 87, 272): Vertical tolerance for line grouping
- `IAF_START_RE` (line 22): Regex for IAF sector headers
- `HEAD_RE` (line 253): Regex for NACE description headers
- Alignment thresholds (lines 181, 194): Y-distance for column matching

### Validation

After extraction, always review `extract_log.txt`:
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

### Extending the API

`api_server.py` uses FastAPI with Pydantic models:
- Add new endpoints to `app`
- Use `MAPPING` global (preloaded at startup)
- Helper `_get_sector()` retrieves full sector by IAF code
