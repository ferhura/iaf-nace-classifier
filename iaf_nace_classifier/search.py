"""
Búsqueda inversa de actividades empresariales → códigos NACE/IAF

Este módulo permite buscar códigos NACE y sectores IAF a partir de
descripciones de actividades empresariales usando búsqueda por relevancia.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .mapping import load_mapping
from .data.risks import get_risks_for_iaf


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para búsqueda: minúsculas, sin acentos.

    Args:
        texto: Texto a normalizar

    Returns:
        Texto normalizado en minúsculas y sin acentos
    """
    if not texto:
        return ""
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


def calcular_relevancia(query: str, descripcion: str, synonyms: Dict[str, str] = None) -> float:
    """Calcula un score de relevancia entre la query y la descripción.

    El score se basa en:
    - Coincidencia exacta de frase: +100 puntos
    - Palabras clave individuales (o sus sinónimos): +5 a +15 puntos cada una
    - Densidad de coincidencias: +0 a +20 puntos

    Args:
        query: Texto de búsqueda (normalizado)
        descripcion: Descripción NACE donde buscar
        synonyms: Diccionario de sinónimos {palabra: sinonimo}

    Returns:
        Score de relevancia (mayor = más relevante)
    """
    if synonyms is None:
        synonyms = {}

    # Normalizar texto descripción
    desc_norm = normalizar_texto(descripcion)
    # query ya viene normalizada desde buscar_actividad
    query_norm = query
    
    # Detectar exclusiones explícitas
    exclusion_phrases = [
        'esta clase no comprende', 
        'este grupo no comprende', 
        'esta división no comprende', 
        'esta division no comprende',
        'no comprende'
    ]
    exclusion_text = ""
    
    for phrase in exclusion_phrases:
        if phrase in desc_norm:
            parts = desc_norm.split(phrase, 1)
            desc_norm = parts[0] # El texto principal es lo que hay ANTES de la exclusión
            exclusion_text = parts[1] # El texto de exclusión es lo que hay DESPUÉS
            break

    # Extraer palabras clave (ignorar palabras comunes)
    stopwords = {
        'el', 'la', 'los', 'las', 'de', 'del', 'y', 'o', 'a', 'en', 'con', 'por', 'para',
        'que', 'esta', 'este', 'esta', 'un', 'una', 'unos', 'unas', 'se', 'su', 'sus',
        'excepto', 'no', 'comprende', 'clase', 'vease', 'incluye', 'excluye'
    }
    palabras_query = [p for p in re.findall(r'\w+', query_norm) if len(p) > 2 and p not in stopwords]

    if not palabras_query:
        return 0.0, 0.0, None

    # Separar título (primera línea) del cuerpo
    parts = desc_norm.split('\n', 1)
    title_norm = parts[0]
    body_norm = parts[1] if len(parts) > 1 else ""

    # Palabras genéricas que aportan poca información específica
    GENERIC_TERMS = {
        'fabricacion', 'produccion', 'manufactura', 'elaboracion', 'confeccion',
        'comercio', 'venta', 'distribucion', 'tienda', 'almacen', 'mayor', 'menor',
        'reparacion', 'mantenimiento', 'instalacion',
        'servicios', 'actividades', 'construccion', 'trabajos',
        'productos', 'articulos', 'bienes', 'materiales', 'equipos', 'maquinas', 'maquinaria', 'sistemas',
        'industrial', 'industriales'
    }

    def _calc_score(text_norm, weight=1.0):
        if not text_norm:
            return 0.0
            
        local_score = 0.0
        words_found_count = 0
        
        # Palabras clave
        for palabra in palabras_query:
            match_found = False
            term_to_score = palabra
            
            # 1. Buscar palabra exacta
            if palabra in text_norm:
                match_found = True
            
            # 2. Buscar sinónimo (si no se encontró la exacta)
            elif palabra in synonyms:
                synonym = synonyms[palabra]
                if synonym in text_norm:
                    match_found = True
                    term_to_score = synonym # Puntuar basado en el sinónimo si es lo que encontramos
            
            if match_found:
                words_found_count += 1
                base_points = 15.0  # Puntos base
                
                # Si el término encontrado es genérico, dar menos puntos
                if term_to_score in GENERIC_TERMS:
                    base_points = 2.0
                
                # Bonus por palabra completa (boundary)
                # Buscamos tanto la palabra original como el sinónimo si aplica
                regex_pattern = r'\b' + re.escape(term_to_score) + r'\b'
                if re.search(regex_pattern, text_norm):
                    local_score += base_points
                else:
                    local_score += base_points * 0.5

        # Densidad (basada en palabras originales de la query)
        if len(palabras_query) > 0:
            densidad = words_found_count / len(palabras_query)
            local_score += densidad * 20.0

        # Frases (bigramas)
        # Generar bigramas del texto
        text_words = [p for p in re.findall(r'\w+', text_norm) if len(p) > 2 and p not in stopwords]
        text_bigrams = set()
        if len(text_words) > 1:
            for i in range(len(text_words) - 1):
                text_bigrams.add(f"{text_words[i]} {text_words[i+1]}")

        # Bigramas de la query
        if len(palabras_query) > 1:
            for i in range(len(palabras_query) - 1):
                w1 = palabras_query[i]
                w2 = palabras_query[i+1]
                
                # Combinaciones posibles:
                # 1. w1 + w2 (Exacto)
                # 2. syn(w1) + w2
                # 3. w1 + syn(w2)
                # 4. syn(w1) + syn(w2)
                
                candidates = []
                candidates.append(f"{w1} {w2}")
                if w1 in synonyms: candidates.append(f"{synonyms[w1]} {w2}")
                if w2 in synonyms: candidates.append(f"{w1} {synonyms[w2]}")
                if w1 in synonyms and w2 in synonyms: candidates.append(f"{synonyms[w1]} {synonyms[w2]}")
                
                match_bigram = False
                matched_candidate = ""
                
                for cand in candidates:
                    if cand in text_bigrams:
                        match_bigram = True
                        matched_candidate = cand
                        break
                
                if match_bigram:
                    # Verificar si el bigram está compuesto solo por términos genéricos
                    cw1, cw2 = matched_candidate.split()
                    if cw1 in GENERIC_TERMS and cw2 in GENERIC_TERMS:
                         local_score += 5.0
                    else:
                         local_score += 30.0
        
        return local_score * weight

    # Calcular score total: Título (x2) + Cuerpo (x1)
    score = _calc_score(title_norm, weight=2.0) + _calc_score(body_norm, weight=1.0)
    base_score = score
    exclusion_hit = None

    # Penalización por exclusiones
    if exclusion_text:
        exclusion_words = [p for p in re.findall(r'\w+', exclusion_text) if len(p) > 2 and p not in stopwords]
        segmentos = re.split(r'[,;]|\by\b', exclusion_text)
        
        for segmento in segmentos:
            seg_words = [p for p in re.findall(r'\w+', segmento) if len(p) > 2 and p not in stopwords]
            if not seg_words:
                continue
                
            query_words_set = set(palabras_query)
            # Añadir sinónimos al set de query para la comprobación de exclusión
            for q in palabras_query:
                if q in synonyms:
                    query_words_set.add(synonyms[q])
            
            positive_title = title_norm.split('excepto')[0]
            positive_title_words = set(p for p in re.findall(r'\w+', positive_title) if len(p) > 2 and p not in stopwords)
            
            if set(seg_words).issubset(positive_title_words):
                continue

            if len(seg_words) == 1:
                if seg_words[0] in query_words_set:
                    score -= 200.0
                    exclusion_hit = segmento.strip()
                    break
            
            if set(seg_words).issubset(query_words_set):
                score -= 200.0
                exclusion_hit = segmento.strip()
                break
    
    return score, base_score, exclusion_hit


def buscar_actividad(
    query: str,
    actividades_reales: str = "",
    procesos_criticos: str = "",
    mapping: Optional[List[Dict[str, Any]]] = None,
    mapping_path: Optional[str | Path] = None,
    top_n: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """Busca códigos NACE y sectores IAF que coincidan con una descripción de actividad.

    Args:
        query: Descripción de la actividad (ej: "fabricación de muebles")
        actividades_reales: Descripción de actividades reales (opcional)
        procesos_criticos: Descripción de procesos críticos (opcional)
        mapping: Lista de sectores IAF cargada. Si None, se carga desde mapping_path
        mapping_path: Ruta al JSON de mapeo. Si None, usa el archivo por defecto
        top_n: Número máximo de resultados a retornar

    Returns:
        Diccionario con dos listas: 'results' (resultados principales) y 'excluded' (candidatos excluidos).
    """
    if mapping is None:
        if mapping_path is None:
            mapping = load_mapping()
        else:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

    resultados = []
    excluidos = []

    # Combinar campos para la búsqueda
    full_query_text = f"{query} {actividades_reales} {procesos_criticos}".strip()
    query_norm_full = normalizar_texto(full_query_text)
    
    if query and query.strip():
        query_norm_intent = normalizar_texto(query)
    else:
        query_norm_intent = query_norm_full
    
    intent_manufacturing = any(w in query_norm_intent for w in ['fabricacion', 'fabricación', 'fabrica', 'fábrica', 'produccion', 'producción', 'manufactura', 'elaboracion', 'elaboración', 'confeccion', 'confección'])
    intent_trade = any(w in query_norm_intent for w in ['comercio', 'venta', 'distribucion', 'distribución', 'tienda', 'almacen', 'almacén', 'mayor', 'menor'])

    SYNONYMS = {
        'computadora': 'ordenador',
        'computadoras': 'ordenadores',
        'laptop': 'ordenador',
        'laptops': 'ordenadores',
        'pc': 'ordenador',
        'celular': 'telefono',
        'celulares': 'telefonos',
        'movil': 'telefono',
        'moviles': 'telefonos',
        'carro': 'vehiculo',
        'carros': 'vehiculos',
        'auto': 'vehiculo',
        'autos': 'vehiculos',
        'coche': 'vehiculo',
        'coches': 'vehiculos',
        'camion': 'vehiculo',
        'camiones': 'vehiculos',
        'software': 'informatica',
        'app': 'informatica',
        'apps': 'informatica',
        'web': 'informatica',
        'internet': 'informatica',
        'consultoria': 'consultores',
        'asesoria': 'consultores',
        'tienda': 'comercio',
        'almacen': 'comercio',
        'bodega': 'almacenamiento',
        'basura': 'desechos',
        'basuras': 'desechos',
        'residuos': 'desechos',
        'hospital': 'asistencia',
        'clinica': 'asistencia',
        'medico': 'asistencia',
        'salud': 'asistencia',
        'educacion': 'enseñanza',
        'escuela': 'enseñanza',
        'colegio': 'enseñanza',
        'universidad': 'enseñanza',
        'restaurante': 'comidas',
        'bar': 'bebidas',
        'cafeteria': 'bebidas',
        'hotel': 'alojamiento',
        'hostal': 'alojamiento',
        'turismo': 'agencias',
        'viajes': 'agencias',
        'reciclaje': 'valorizacion',
        'reciclar': 'valorizacion',
        'chatarra': 'desechos',
        'desperdicios': 'desechos',
        'barco': 'buque',
        'barcos': 'buques',
        'embarcacion': 'buque',
        'embarcaciones': 'buques',
        'joyas': 'joyeria',
        'joya': 'joyeria',
        'digital': 'graficas',
        'sorting': 'clasificacion',
        'scrap': 'chatarra',
        'waste': 'residuos',
        'aparthoteles': 'hoteles',
        'cervecerias': 'bares',
        'notaria': 'notarios',
        'notario': 'notarios',
        'abogado': 'juridicas',
        'abogados': 'juridicas',
        'bufete': 'juridicas',
        'maquinados': 'mecanica',
        'maquinado': 'mecanica',
        'mecanizado': 'mecanica',
        'saas': 'informatica',
        'cloud': 'informatica',
        'ecommerce': 'internet',
        'ciberseguridad': 'informatica',
        'blockchain': 'informatica',
        'bigdata': 'datos',
        'desarrollador': 'programacion',
        'programador': 'programacion',
        'seo': 'publicidad',
        'sem': 'publicidad',
        'community': 'publicidad',
        'picking': 'almacenamiento',
        'packing': 'envasado',
        'delivery': 'correos',
        'rider': 'correos',
        'paqueteria': 'postal',
        'envios': 'postal',
        'pladur': 'revocamiento',
        'drywall': 'revocamiento',
        'albañileria': 'construccion',
        'reformas': 'construccion',
        'fotovoltaica': 'electrica',
        'solar': 'electrica',
        'eolica': 'electrica',
        'biomasa': 'electrica',
        'renovables': 'electrica',
        'callcenter': 'llamadas',
        'contactcenter': 'llamadas',
        'coworking': 'inmobiliarias',
        'agrotech': 'agricultura',
        'hidroponia': 'cultivos',
        'mineria': 'extraccion',
        'excavacion': 'extraccion',
        'aridos': 'grava',
        'snacks': 'alimenticios',
        'vegan': 'alimenticios',
        'gourmet': 'alimenticios',
        'moda': 'confeccion',
        'fashion': 'confeccion',
        'ebanisteria': 'muebles',
        'aserradero': 'aserrado',
        'packaging': 'envases',
        'periodismo': 'agencias',
        'rotulacion': 'impresion',
        '3d': 'impresion',
        'cosmetica': 'perfumes',
        'perfumeria': 'perfumes',
        'biotech': 'investigacion',
        'laboratorio': 'ensayos',
        'polimeros': 'plasticos',
        'prefabricados': 'hormigon',
        'cnc': 'mecanica',
        'torneria': 'mecanica',
        'caldereria': 'estructuras',
        'robotica': 'maquinaria',
        'automatizacion': 'maquinaria',
        'chips': 'componentes',
        'sensores': 'instrumentos',
        'astillero': 'barcos',
        'yates': 'barcos',
        'drones': 'aeronautica',
        'trenes': 'ferroviario',
        'chatarreria': 'residuos',
        'biogas': 'gas',
        'depuradora': 'alcantarillado',
        'electricista': 'instalaciones',
        'retail': 'menor',
        'concesionario': 'vehiculos',
        'taller': 'mantenimiento',
        'hosteleria': 'restaurantes',
        'turismo': 'agencias',
        'mudanzas': 'transporte',
        'fintech': 'financieros',
        'devops': 'informatica',
        'agile': 'consultoria',
        'project': 'consultoria',
        'facility': 'limpieza',
        'ayuntamiento': 'publica',
        'elearning': 'educacion',
        'bootcamp': 'educacion',
        'master': 'educacion',
        'fisioterapia': 'sanitarias',
        'estetica': 'belleza',
        'wellness': 'fisico',
        'ong': 'asociativas',
        'fundacion': 'asociativas',
        'voluntariado': 'social',
        'navidad': 'regalo',
        'navideñas': 'regalo',
        'navidenas': 'regalo',
        'adornos': 'regalo',
        'decoracion': 'regalo',
        'dolor': 'medicina',
        'universitaria': 'educacion',
    
        # Calzado / Zapatos
        'zapatos': 'calzado',
        'zapato': 'calzado',
        'zapatillas': 'calzado',
        'botas': 'calzado',
        'sandalias': 'calzado',
        'tenis': 'calzado',
    }

    # NO expandimos la query concatenando strings.
    # Pasamos el mapa de sinónimos a calcular_relevancia para que lo use inteligentemente.

    for sector in mapping:
        codigo_iaf = sector.get('codigo_iaf')
        nombre_iaf = sector.get('nombre_iaf', '')
        riesgos_sector = get_risks_for_iaf(codigo_iaf)

        for desc_obj in sector.get('descripcion_nace', []):
            codigo_nace = desc_obj.get('codigo')
            descripcion = desc_obj.get('descripcion', '')

            # Pasamos query_norm_full (texto original normalizado) y los sinónimos
            score, base_score, exclusion_hit = calcular_relevancia(query_norm_full, descripcion, synonyms=SYNONYMS)
            
            if score > 0 or (base_score > 50 and exclusion_hit):
                try:
                    nace_div = int(codigo_nace.split('.')[0])
                except (ValueError, IndexError):
                    nace_div = 0

                if intent_manufacturing:
                    if 10 <= nace_div <= 33:
                        pass
                    elif 45 <= nace_div <= 47:
                        score -= 200.0
                    elif nace_div < 10:
                        score -= 50.0

                elif intent_trade:
                    if 45 <= nace_div <= 47:
                        score += 50.0
                    elif 10 <= nace_div <= 33:
                        score -= 200.0

                software_keywords = [
                    'software', 'programacion', 'informatica', 'computadora', 'ordenador', 
                    'app', 'web', 'digital', 'datos', 'sistema', 'red', 'servidor', 'cloud', 'nube',
                    'virtual', 'internet', 'online', 'ciber', 'tecnologia'
                ]
                intent_software = any(w in query_norm_intent for w in software_keywords)
                
                if intent_software:
                    if nace_div in [62, 63] or codigo_nace.startswith('58.2'):
                        score += 100.0

                    is_physical_sector = (
                        (1 <= nace_div <= 3) or
                        (5 <= nace_div <= 9) or
                        (10 <= nace_div <= 33 and nace_div != 26) or
                        (41 <= nace_div <= 43) or
                        (49 <= nace_div <= 53) or
                        (nace_div == 56) or
                        (nace_div == 81)
                    )
                    
                    if is_physical_sector:
                        score -= 200.0

                intent_personal = any(w in query_norm_intent for w in ['pelo', 'cabello', 'peluqueria', 'estetica', 'belleza', 'manicura'])
                if intent_personal:
                    if (10 <= nace_div <= 33) or (41 <= nace_div <= 43):
                        score -= 200.0

                intent_medical = any(w in query_norm_intent for w in ['medico', 'medica', 'cirugia', 'operacion', 'paciente', 'hospital', 'clinica', 'salud', 'enfermeria', 'dolor'])
                if intent_medical:
                    if 64 <= nace_div <= 70:
                        score -= 200.0
                    if 10 <= nace_div <= 33 and nace_div not in [21, 26, 32]:
                        score -= 50.0

                intent_decoration = any(w in query_norm_intent for w in ['navidad', 'navideñas', 'navidenas', 'adornos', 'decoracion', 'fiesta', 'regalo'])
                if intent_decoration:
                    if codigo_nace == '26.52':
                        score -= 200.0
                    if codigo_nace == '32.99':
                        score += 50.0

                if score > 0:
                    resultados.append({
                        'codigo_nace': codigo_nace,
                        'descripcion_nace': descripcion[:300] + '...' if len(descripcion) > 300 else descripcion,
                        'descripcion_completa': descripcion,
                        'codigo_iaf': codigo_iaf,
                        'nombre_iaf': nombre_iaf,
                        'relevancia': score,
                        'riesgos': riesgos_sector
                    })
                elif base_score > 100 and exclusion_hit:
                    excluidos.append({
                        'codigo_nace': codigo_nace,
                        'descripcion_nace': descripcion[:300] + '...' if len(descripcion) > 300 else descripcion,
                        'descripcion_completa': descripcion,
                        'codigo_iaf': codigo_iaf,
                        'nombre_iaf': nombre_iaf,
                        'relevancia': base_score,
                        'razon_exclusion': exclusion_hit
                    })

    resultados.sort(key=lambda x: x['relevancia'], reverse=True)
    excluidos.sort(key=lambda x: x['relevancia'], reverse=True)

    MIN_SCORE_THRESHOLD = 20.0
    
    if resultados:
        max_score = resultados[0]['relevancia']
        if max_score < MIN_SCORE_THRESHOLD:
            resultados = []
        else:
            threshold = max_score * 0.5
            resultados = [r for r in resultados if r['relevancia'] >= threshold]

    return {
        'results': resultados[:top_n],
        'excluded': excluidos[:3]
    }
