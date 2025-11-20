#!/usr/bin/env python3
"""
Búsqueda inversa: actividad empresarial → códigos NACE → sectores IAF

Uso:
    python buscar_actividad.py "fabricación de productos metálicos"
    python buscar_actividad.py "restaurante" --top 5
    python buscar_actividad.py "cultivo de tomates" --json
"""

import argparse
import json
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para búsqueda: minúsculas, sin acentos, sin puntuación extra."""
    texto = texto.lower()
    # Quitar acentos comunes
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'ñ': 'n'
    }
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    return texto


def calcular_relevancia(query: str, descripcion: str) -> float:
    """Calcula un score de relevancia entre la query y la descripción."""
    query_norm = normalizar_texto(query)
    desc_norm = normalizar_texto(descripcion)

    # Extraer palabras clave (ignorar palabras comunes)
    stopwords = {'el', 'la', 'los', 'las', 'de', 'del', 'y', 'o', 'a', 'en', 'con', 'por', 'para',
                 'que', 'esta', 'este', 'esta', 'un', 'una', 'unos', 'unas', 'se', 'su', 'sus'}
    palabras_query = [p for p in re.findall(r'\w+', query_norm) if len(p) > 2 and p not in stopwords]

    if not palabras_query:
        return 0.0

    score = 0.0

    # Coincidencia exacta de frase completa (máxima prioridad)
    if query_norm in desc_norm:
        score += 100.0

    # Contar cuántas palabras clave aparecen
    for palabra in palabras_query:
        if palabra in desc_norm:
            # Bonus si aparece como palabra completa (con límites)
            if re.search(r'\b' + re.escape(palabra) + r'\b', desc_norm):
                score += 10.0
            else:
                score += 5.0

    # Bonus por densidad de palabras clave
    palabras_encontradas = sum(1 for p in palabras_query if p in desc_norm)
    densidad = palabras_encontradas / len(palabras_query)
    score += densidad * 20.0

    return score


def buscar_actividad(
    query: str,
    mapping_path: str = "iaf_nace_mapeo_expandido.json",
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca códigos NACE y sectores IAF que coincidan con una descripción de actividad.

    Returns:
        Lista de resultados ordenados por relevancia, cada uno con:
        - codigo_nace: código NACE encontrado
        - descripcion_nace: descripción del código
        - codigo_iaf: sector IAF al que pertenece
        - nombre_iaf: nombre del sector IAF
        - relevancia: score de relevancia
    """
    # Cargar mapeo
    with open(mapping_path, 'r', encoding='utf-8') as f:
        sectores = json.load(f)

    resultados = []

    # Buscar en todas las descripciones NACE
    for sector in sectores:
        codigo_iaf = sector.get('codigo_iaf')
        nombre_iaf = sector.get('nombre_iaf', '')

        for desc_obj in sector.get('descripcion_nace', []):
            codigo_nace = desc_obj.get('codigo')
            descripcion = desc_obj.get('descripcion', '')

            # Calcular relevancia
            score = calcular_relevancia(query, descripcion)

            if score > 0:
                resultados.append({
                    'codigo_nace': codigo_nace,
                    'descripcion_nace': descripcion[:300] + '...' if len(descripcion) > 300 else descripcion,
                    'descripcion_completa': descripcion,
                    'codigo_iaf': codigo_iaf,
                    'nombre_iaf': nombre_iaf,
                    'relevancia': score
                })

    # Ordenar por relevancia (mayor a menor)
    resultados.sort(key=lambda x: x['relevancia'], reverse=True)

    return resultados[:top_n]


def main():
    parser = argparse.ArgumentParser(
        description="Busca códigos NACE e IAF a partir de una descripción de actividad empresarial"
    )
    parser.add_argument(
        "actividad",
        help="Descripción de la actividad (ej: 'fabricación de muebles', 'restaurante', 'cultivo de frutas')"
    )
    parser.add_argument(
        "--mapping", "-m",
        default="iaf_nace_mapeo_expandido.json",
        help="Ruta al archivo JSON de mapeo (por defecto: iaf_nace_mapeo_expandido.json)"
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=10,
        help="Número máximo de resultados a mostrar (por defecto: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Mostrar resultados en formato JSON"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Mostrar descripciones completas (no truncadas)"
    )

    args = parser.parse_args()

    # Buscar
    resultados = buscar_actividad(args.actividad, args.mapping, args.top)

    if not resultados:
        print(f"No se encontraron coincidencias para: '{args.actividad}'")
        return 1

    if args.json:
        # Salida JSON
        output = []
        for r in resultados:
            output.append({
                'codigo_nace': r['codigo_nace'],
                'codigo_iaf': r['codigo_iaf'],
                'nombre_iaf': r['nombre_iaf'],
                'relevancia': r['relevancia'],
                'descripcion': r['descripcion_completa'] if args.full else r['descripcion_nace']
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Salida formato texto
        print(f"\n🔍 Resultados para: '{args.actividad}'")
        print(f"{'='*80}\n")

        for i, r in enumerate(resultados, 1):
            print(f"{i}. NACE {r['codigo_nace']} → IAF {r['codigo_iaf']} ({r['nombre_iaf']})")
            print(f"   Relevancia: {r['relevancia']:.1f}")

            desc = r['descripcion_completa'] if args.full else r['descripcion_nace']
            # Formatear descripción con indentación
            for line in desc.split('\n'):
                if line.strip():
                    print(f"   {line.strip()}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
