# Guía de Búsqueda de Actividades → NACE/IAF

## ¿Qué es esto?

Esta herramienta te permite encontrar códigos NACE e IAF a partir de una descripción de la actividad empresarial. Es la búsqueda **inversa** del clasificador principal.

**Flujo normal del clasificador:**
```
Código NACE (ej: "24.46") → Sector IAF
```

**Flujo de esta herramienta:**
```
Descripción de actividad (ej: "restaurante") → Códigos NACE + Sectores IAF
```

## Uso desde línea de comandos

### Búsqueda básica

```bash
python buscar_actividad.py "fabricación de muebles"
```

Esto mostrará los 10 códigos NACE más relevantes con sus sectores IAF correspondientes.

### Limitar número de resultados

```bash
python buscar_actividad.py "restaurante" --top 3
```

### Salida en JSON

```bash
python buscar_actividad.py "cultivo de frutas" --json
```

### Ver descripciones completas

```bash
python buscar_actividad.py "software" --full
```

### Usar archivo de mapeo personalizado

```bash
python buscar_actividad.py "agricultura" -m mi_mapeo.json
```

## Uso desde Python

```python
from buscar_actividad import buscar_actividad

# Buscar actividad
resultados = buscar_actividad("fabricación de productos metálicos", top_n=5)

# Iterar resultados
for r in resultados:
    print(f"NACE: {r['codigo_nace']}")
    print(f"IAF: {r['codigo_iaf']} - {r['nombre_iaf']}")
    print(f"Relevancia: {r['relevancia']}")
    print(f"Descripción: {r['descripcion_nace']}")
    print()

# Obtener solo el mejor resultado
mejor = resultados[0] if resultados else None
if mejor:
    codigo_nace = mejor['codigo_nace']
    codigo_iaf = mejor['codigo_iaf']

    # Ahora puedes usar este código con el clasificador
    from iaf_nace_classifier import classify_nace, load_mapping
    mapping = load_mapping()
    clasificacion = classify_nace(codigo_nace, mapping)
```

## Ejemplos de uso

### Ejemplo 1: Empresa de desarrollo de software

```bash
$ python buscar_actividad.py "desarrollo de software" --top 3

🔍 Resultados para: 'desarrollo de software'
================================================================================

1. NACE 62.01 → IAF 33 (Información tecnológica)
   Relevancia: 140.0
   62.01 Actividades de programación informática
   Esta clase comprende la escritura, modificación, prueba y asistencia del
   software diseñado para atender las necesidades de un cliente determinado...
```

### Ejemplo 2: Restaurante

```bash
$ python buscar_actividad.py "restaurante comida rápida" --top 3

🔍 Resultados para: 'restaurante comida rápida'
================================================================================

1. NACE 56.10 → IAF 30 (Hoteles y restaurantes)
   Relevancia: 35.0
   56.10 Restaurantes y puestos de comidas
   Esta clase comprende la prestación de servicios de comida a clientes...
```

### Ejemplo 3: Agricultura

```bash
$ python buscar_actividad.py "cultivo de tomates y hortalizas" --top 3

🔍 Resultados para: 'cultivo de tomates y hortalizas'
================================================================================

1. NACE 01.13 → IAF 1 (Agricultura, pesca)
   Relevancia: 150.0
   01.13 Cultivo de hortalizas, raíces y tubérculos
   Esta clase comprende:
   - el cultivo de hortalizas de hoja o tallo...
```

### Ejemplo 4: Fabricación

```bash
$ python buscar_actividad.py "fabricación de muebles de madera" --json

[
  {
    "codigo_nace": "31",
    "codigo_iaf": 23,
    "nombre_iaf": "Fabricación no clasificada en otra parte",
    "relevancia": 150.0,
    "descripcion": "31 Fabricación de muebles..."
  }
]
```

## Cómo funciona el algoritmo de búsqueda

El sistema calcula un **score de relevancia** basándose en:

1. **Coincidencia exacta de frase** (+100 puntos): Si la búsqueda aparece textualmente en la descripción
2. **Palabras clave individuales** (+5 a +10 puntos cada una): Según si aparecen como palabra completa o como parte de otra
3. **Densidad de coincidencias** (+0 a +20 puntos): Porcentaje de palabras clave encontradas

### Normalización de texto

- Convierte todo a minúsculas
- Elimina acentos (á → a, é → e, etc.)
- Ignora palabras comunes (stopwords): "el", "la", "de", "y", etc.

## Integración con el clasificador

Una vez que encuentres el código NACE apropiado, puedes usarlo con el clasificador principal:

```python
from buscar_actividad import buscar_actividad
from iaf_nace_classifier import classify_nace, load_mapping

# 1. Buscar por actividad
resultados = buscar_actividad("mi actividad empresarial")
mejor_match = resultados[0] if resultados else None

# 2. Obtener código NACE
codigo_nace = mejor_match['codigo_nace']

# 3. Clasificar con el sistema principal
mapping = load_mapping()
clasificacion = classify_nace(codigo_nace, mapping)

print(f"IAF: {clasificacion['codigo_iaf']}")
print(f"Sector: {clasificacion['nombre_iaf']}")
```

## Casos de uso

### Caso 1: Clasificación automática de empresas

Si tienes una base de datos de empresas con descripciones de actividad, puedes clasificarlas automáticamente:

```python
empresas = [
    {"nombre": "Empresa A", "actividad": "desarrollo de aplicaciones móviles"},
    {"nombre": "Empresa B", "actividad": "restaurante italiano"},
    {"nombre": "Empresa C", "actividad": "cultivo de naranjas"},
]

for empresa in empresas:
    resultados = buscar_actividad(empresa['actividad'], top_n=1)
    if resultados:
        mejor = resultados[0]
        print(f"{empresa['nombre']}: NACE {mejor['codigo_nace']}, IAF {mejor['codigo_iaf']}")
```

### Caso 2: Validación manual

Usa la herramienta para explorar opciones y seleccionar manualmente el código más apropiado:

```bash
python buscar_actividad.py "mi actividad" --top 10
# Revisar los resultados
# Elegir el código NACE más apropiado
python -m iaf_nace_classifier.cli <codigo_elegido>
```

## Limitaciones

- **Solo búsqueda en español**: Las descripciones están en español
- **Calidad de coincidencia**: Depende de qué tan bien describas la actividad
- **Términos técnicos**: Usa terminología similar a la del documento NACE oficial
- **Ambigüedad**: Actividades muy genéricas pueden dar muchos resultados poco específicos

## Tips para mejores resultados

1. **Sé específico**: "fabricación de muebles de madera" es mejor que "muebles"
2. **Usa términos técnicos**: "servicios de consultoría informática" vs "informática"
3. **Incluye palabras clave**: "cultivo", "fabricación", "servicios", "comercio", etc.
4. **Revisa varios resultados**: El primero no siempre es el más apropiado para tu caso
5. **Compara descripciones**: Usa `--full` para ver descripciones completas y comparar

## Ayuda

```bash
python buscar_actividad.py --help
```
