#!/usr/bin/env python3
"""
Ejemplo de uso programático de la búsqueda de actividades
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para poder importar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from iaf_nace_classifier import buscar_actividad, classify_nace, load_mapping

# Ejemplo 1: Buscar actividad de fabricación
print("=" * 80)
print("Ejemplo 1: Fabricación de muebles de madera")
print("=" * 80)
resultados = buscar_actividad("fabricación de muebles de madera", top_n=3)

for r in resultados:
    print(f"\nNACE: {r['codigo_nace']}")
    print(f"IAF:  {r['codigo_iaf']} - {r['nombre_iaf']}")
    print(f"Score: {r['relevancia']:.1f}")
    print(f"Descripción: {r['descripcion_nace']}")

# Ejemplo 2: Buscar actividad de servicios
print("\n" + "=" * 80)
print("Ejemplo 2: Servicios de consultoría informática")
print("=" * 80)
resultados = buscar_actividad("consultoría informática", top_n=3)

for r in resultados:
    print(f"\nNACE: {r['codigo_nace']} → IAF: {r['codigo_iaf']} ({r['nombre_iaf']})")
    print(f"Relevancia: {r['relevancia']:.1f}")

# Ejemplo 3: Obtener el mejor resultado
print("\n" + "=" * 80)
print("Ejemplo 3: Obtener solo el mejor match para 'cultivo de tomates'")
print("=" * 80)
resultados = buscar_actividad("cultivo de tomates", top_n=1)

if resultados:
    mejor = resultados[0]
    print(f"\nMejor coincidencia:")
    print(f"  NACE: {mejor['codigo_nace']}")
    print(f"  IAF:  {mejor['codigo_iaf']} - {mejor['nombre_iaf']}")
    print(f"  Relevancia: {mejor['relevancia']:.1f}")

    # Ahora puedes usar este código NACE con el clasificador
    mapping = load_mapping()
    clasificacion = classify_nace(mejor['codigo_nace'], mapping)
    print(f"\n  Clasificación confirmada: {clasificacion}")
