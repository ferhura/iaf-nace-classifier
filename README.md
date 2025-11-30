# Clasificador IAF–NACE (ES)

Mapea códigos NACE (UE) a sectores IAF y adjunta las descripciones NACE completas de todos los niveles jerárquicos.

## 📋 Características

- **Clasificación NACE → IAF**: Mapeo bidireccional con reglas de especificidad y exclusiones
- **Búsqueda inversa**: Encuentra códigos NACE a partir de descripciones de actividades
- **API HTTP**: Servidor FastAPI para integración web
- **CLI**: Herramientas de línea de comandos
- **Extractor PDF**: Regenera el mapeo desde el documento oficial
- **Instalable**: Compatible con `pip install`

## 📁 Estructura del Proyecto

```
iaf-nace-classifier/
├── README.md                           # Este archivo
├── CLAUDE.md                           # Guía para Claude Code
├── pyproject.toml                      # Configuración del paquete
│
├── iaf_nace_classifier/                # 📦 Paquete principal
│   ├── __init__.py                     # API pública
│   ├── mapping.py                      # Clasificación NACE → IAF
│   ├── search.py                       # Búsqueda inversa de actividades
│   ├── cli.py                          # CLI de clasificación
│   └── api.py                          # Servidor HTTP FastAPI
│
├── data/                               # 📊 Datos y recursos
│   ├── Codigo_NACE_sectoresema.pdf     # Documento fuente
│   └── iaf_nace_mapeo_expandido.json   # Mapeo generado
│
├── scripts/                            # 🛠️ Utilidades
│   ├── extract_iaf_nace.py             # Extractor desde PDF
│   └── buscar_actividad.py             # CLI de búsqueda
│
├── examples/                           # 💡 Ejemplos de uso
│   └── ejemplo_busqueda.py
│
└── docs/                               # 📚 Documentación
    └── GUIA_BUSQUEDA.md                # Guía de búsqueda de actividades
```

## 🚀 Instalación

### Instalación básica (clasificador)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/iaf-nace-classifier.git
cd iaf-nace-classifier

# Instalar en modo editable
pip install -e .
```

### Instalación con API HTTP

```bash
pip install -e ".[api]"
```

### Instalación con extractor PDF

```bash
pip install -e ".[extractor]"
```

### Instalación completa

```bash
pip install -e ".[api,extractor,dev]"
```

### Requisitos

- Python >= 3.10
- Sin dependencias para uso básico (clasificación)
- FastAPI + Uvicorn para API HTTP (opcional)
- PyMuPDF para extractor PDF (opcional)

## 🎯 Uso Rápido

### 1. Clasificación: NACE → IAF

**CLI:**
```bash
# Clasificar un código NACE
python -m iaf_nace_classifier.cli 24.46

# Salida en JSON
python -m iaf_nace_classifier.cli 47 --json
```

**Python:**
```python
from iaf_nace_classifier import classify_nace, load_mapping

mapping = load_mapping()
result = classify_nace("24.46", mapping)
print(result)
# {'codigo_iaf': 18, 'nombre_iaf': 'Maquinaria y equipo',
#  'matched_pattern': '24.46', 'nace_code': '24.46'}
```

### 2. Búsqueda inversa: Actividad → NACE/IAF

**CLI:**
```bash
# Buscar códigos por descripción de actividad
python scripts/buscar_actividad.py "fabricación de muebles" --top 5

# Salida en JSON
python scripts/buscar_actividad.py "restaurante" --json
```

**Python:**
```python
from iaf_nace_classifier import buscar_actividad

# Buscar actividad
resultados = buscar_actividad("desarrollo de software", top_n=3)

for r in resultados:
    print(f"NACE: {r['codigo_nace']} → IAF: {r['codigo_iaf']}")
    print(f"Sector: {r['nombre_iaf']}")
    print(f"Relevancia: {r['relevancia']:.1f}")
```

Ver [docs/GUIA_BUSQUEDA.md](docs/GUIA_BUSQUEDA.md) para más detalles.

### 3. API HTTP

**Iniciar servidor:**
```bash
# Asegúrate de tener instaladas las dependencias de API
pip install -e ".[api]"

# Iniciar servidor
uvicorn iaf_nace_classifier.api:app --reload
```

**Endpoints:**
```bash
# Health check
curl http://127.0.0.1:8000/health

# GET: Clasificar código
curl 'http://127.0.0.1:8000/classify?code=24.46'

# POST: Clasificar código
curl -X POST http://127.0.0.1:8000/classify \
  -H 'Content-Type: application/json' \
  -d '{"code":"47"}'
```

**Respuesta:**
```json
{
  "input": "24.46",
  "result": {
    "codigo_iaf": 18,
    "nombre_iaf": "Maquinaria y equipo",
    "matched_pattern": "24.46",
    "nace_code": "24.46"
  },
  "sector": {
    "codigo_iaf": 18,
    "nombre_iaf": "Maquinaria y equipo",
    "codigos_nace": ["24", "25", "..."],
    "descripcion_nace": [...]
  }
}
```

## 🔧 Desarrollo

### Regenerar datos desde el PDF

```bash
# Instalar dependencias del extractor
pip install -e ".[extractor]"

# Ejecutar extractor
python scripts/extract_iaf_nace.py
```

**Produce:**
- `data/iaf_nace_mapeo_expandido.json`: Mapeo IAF-NACE con descripciones
- `extract_log.txt`: Métricas y advertencias de validación

### Ejecutar ejemplos

```bash
# Ejemplo de búsqueda
python examples/ejemplo_busqueda.py
```

### Ejecutar tests (próximamente)

```bash
pip install -e ".[dev]"
pytest tests/
```

## 📖 Documentación

### Formato del JSON

Cada sector IAF contiene:
```json
{
  "codigo_iaf": 1,
  "nombre_iaf": "Agricultura, pesca",
  "codigos_nace": ["01", "02", "03"],
  "exclusiones": [],
  "descripcion_nace": [
    {
      "codigo": "01",
      "descripcion": "01 Agricultura, ganadería, caza..."
    },
    {
      "codigo": "01.1",
      "descripcion": "01.1 Cultivos no perennes..."
    }
  ]
}
```

### Reglas de Clasificación

1. **Coincidencia por prefijo**: El patrón más específico gana
   - `24.46` coincide con `24` y `24.46` → gana `24.46`
2. **Exclusiones**: Respeta prefijos excluidos explícitamente
3. **Normalización**: Acepta `"24"`, `"24.46"`, etc.

### Algoritmo de Búsqueda

La búsqueda inversa calcula un **score de relevancia**:
- Coincidencia exacta de frase: +100 puntos
- Palabras clave individuales: +5 a +10 puntos
- Densidad de coincidencias: +0 a +20 puntos

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📝 Limitaciones

- El extractor PDF está optimizado para el documento incluido
- Si el formato del PDF cambia, puede requerir ajustes
- La búsqueda solo funciona con descripciones en español
- Validar siempre con `extract_log.txt` después de regenerar datos

## 🙏 Créditos

- Extracción: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- API: [FastAPI](https://fastapi.tiangolo.com/)
- Clasificación: Implementación en Python puro

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles
