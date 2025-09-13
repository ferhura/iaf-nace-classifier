Clasificador IAF–NACE (ES)

Descripción
- Mapea códigos NACE (UE) a sectores IAF y adjunta las descripciones NACE completas de todos los niveles (p. ej. `01`, `01.1`, `01.11`, …).
- Incluye un extractor desde el PDF `Codigo_NACE_sectoresema.pdf`, un JSON listo para usar y un CLI/API en Python para clasificar códigos.

Instalación
- Requisitos: `Python >= 3.10`.
- Para usar el clasificador (CLI/API) no se requieren dependencias extra.
- Para regenerar el JSON desde el PDF: `pip install PyMuPDF` (módulo `fitz`).

Uso Rápido (CLI)
- Clasificar un código NACE:
  - `python -m iaf_nace_classifier.cli 24.46`
- Salida en JSON:
  - `python -m iaf_nace_classifier.cli 47 --json`
- Usar un mapeo propio:
  - `python -m iaf_nace_classifier.cli 74.31 -m sectores_iaf_completos.json`

Uso en Python (API)
- Ejemplo:
  - `from iaf_nace_classifier import classify_nace, load_mapping`
  - `mp = load_mapping()`
  - `result = classify_nace("24.46", mp)`
- Devuelve: `{"codigo_iaf": int, "nombre_iaf": str|None, "matched_pattern": str, "nace_code": str}`.

Regenerar Datos desde el PDF
- Ejecuta el extractor:
  - `python extract_iaf_nace.py`
- Produce:
  - `sectores_iaf_completos.json`: lista de sectores IAF con códigos NACE y descripciones completas expandidas a todos los subniveles.
  - `extract_log.txt`: métricas y advertencias de validación.

Cómo Funciona el Extractor
- Tabla de mapeo (página 1):
  - Reconstruye líneas por coordenadas del PDF y alinea columnas nombre/códigos.
  - Une nombres partido en varias líneas y detecta exclusiones tras `excepto`.
- Descripciones NACE (páginas 2..N):
  - Detecta encabezados `NN Título`, `NN.N Título`, `NN.NN Título` y captura el texto completo posterior (párrafos y viñetas) hasta el siguiente encabezado.
- Expansión por niveles:
  - Para cada código base del sector (p. ej. `01`) se incluyen todas las subentradas (`01.1`, `01.11`, …), excluyendo prefijos indicados tras `excepto`.
- Normalización y robustez OCR:
  - Corrige `except0`→`excepto` y normaliza formatos (`01`, `01.11`, etc.).

Formato del JSON
- Cada sector es un objeto con:
  - `codigo_iaf`: número del sector IAF.
  - `nombre_iaf`: nombre del sector IAF.
  - `codigos_nace`: lista de patrones NACE asociados (pueden ser de 2 o 4 caracteres con punto).
  - `exclusiones`: lista de patrones a excluir (prefijos NACE).
  - `descripcion_nace`: lista de objetos `{ "codigo": str, "descripcion": str }` para todos los subniveles incluidos.

Clasificador (Reglas)
- Coincidencia por prefijo: el patrón más específico gana (ej. `24.46` sobre `24`).
- Respeta exclusiones: no asigna a sectores que excluyen explícitamente el prefijo.
- Entrada flexible: acepta `"24"`, `"24.46"`, etc. y normaliza internamente.

Validación
- El archivo `extract_log.txt` resume:
  - Sectores extraídos.
  - Códigos NACE referenciados (sin expandir) y su cobertura de descripciones.
  - Total de códigos descritos tras la expansión por niveles.
  - Advertencias útiles para revisar posibles problemas de OCR/segmentación.

Limitaciones y Notas
- Si el maquetado del PDF cambia, puede requerir ajustar la tolerancia vertical o reglas de encabezado.
- El extractor está afinado para el documento incluido; en PDFs distintos, valida con `extract_log.txt`.
- Puedes editar manualmente `sectores_iaf_completos.json` si necesitas ajustes puntuales.

Créditos
- Extracción basada en `PyMuPDF (fitz)`; clasificación implementada en puro Python.
