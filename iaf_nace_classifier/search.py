"""
Búsqueda inversa de actividades empresariales → códigos NACE/IAF

Este módulo permite buscar códigos NACE y sectores IAF a partir de
descripciones de actividades empresariales usando búsqueda por relevancia.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def calcular_relevancia(query: str, descripcion: str) -> float:
    """Calcula un score de relevancia entre la query y la descripción.

    El score se basa en:
    - Coincidencia exacta de frase: +100 puntos
    - Palabras clave individuales: +5 a +10 puntos cada una
    - Densidad de coincidencias: +0 a +20 puntos

    Args:
        query: Texto de búsqueda
        descripcion: Descripción NACE donde buscar

    Returns:
        Score de relevancia (mayor = más relevante)
    """
    # Normalizar texto
    desc_norm = normalizar_texto(descripcion)
    query_norm = normalizar_texto(query)
    
    # Detectar exclusiones explícitas
    # Solo usamos frases que indican claramente el inicio de una sección de exclusión.
    # Evitamos "excepto" o "excluye" porque pueden aparecer en medio de frases descriptivas.
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
        'productos', 'articulos', 'bienes', 'materiales', 'equipos', 'maquinas', 'sistemas'
    }

    def _calc_score(text_norm, weight=1.0):
        if not text_norm:
            return 0.0
            
        local_score = 0.0
        
        # Palabras clave
        for palabra in palabras_query:
            if palabra in text_norm:
                base_points = 15.0  # Puntos base aumentados para palabras específicas
                
                if palabra in GENERIC_TERMS:
                    base_points = 2.0  # Puntos reducidos para palabras genéricas
                
                if re.search(r'\b' + re.escape(palabra) + r'\b', text_norm):
                    local_score += base_points
                else:
                    local_score += base_points * 0.5

        # Densidad
        palabras_encontradas = sum(1 for p in palabras_query if p in text_norm)
        if len(palabras_query) > 0:
            densidad = palabras_encontradas / len(palabras_query)
            local_score += densidad * 20.0

        # Frases (bigramas)
        # Generar bigramas solo de palabras significativas (sin stopwords)
        # Esto evita que "fabricación de" sume puntos, pero permite que "fabricación muebles" sí lo haga.
        
        # Palabras significativas del texto (normalizado)
        text_words = [p for p in re.findall(r'\w+', text_norm) if len(p) > 2 and p not in stopwords]
        text_bigrams = set()
        if len(text_words) > 1:
            for i in range(len(text_words) - 1):
                text_bigrams.add(f"{text_words[i]} {text_words[i+1]}")

        # Palabras significativas de la query (ya las tenemos en palabras_query)
        if len(palabras_query) > 1:
            for i in range(len(palabras_query) - 1):
                bigram = f"{palabras_query[i]} {palabras_query[i+1]}"
                
                if bigram in text_bigrams:
                    # Verificar si el bigram está compuesto solo por términos genéricos
                    w1, w2 = bigram.split()
                    if w1 in GENERIC_TERMS and w2 in GENERIC_TERMS:
                         local_score += 5.0 # Muy poco valor si ambos son genéricos
                    else:
                         local_score += 30.0  # Bonus alto para frases específicas
        
        return local_score * weight

    # Calcular score total: Título (x2) + Cuerpo (x1)
    score = _calc_score(title_norm, weight=2.0) + _calc_score(body_norm, weight=1.0)
    base_score = score
    exclusion_hit = None

    # Penalización por exclusiones
    # Si una palabra clave aparece en la sección de exclusión, penalizar fuertemente
    if exclusion_text:
        # Analizar palabras de la exclusión
        exclusion_words = [p for p in re.findall(r'\w+', exclusion_text) if len(p) > 2 and p not in stopwords]
        
        # Crear segmentos de exclusión (separados por comas o 'y')
        # Esto es una aproximación. Lo ideal sería un análisis sintáctico más profundo.
        segmentos = re.split(r'[,;]|\by\b', exclusion_text)
        
        for segmento in segmentos:
            seg_words = [p for p in re.findall(r'\w+', segmento) if len(p) > 2 and p not in stopwords]
            if not seg_words:
                continue
                
            # Verificar si TODAS las palabras significativas del segmento están en la query
            # Ejemplo: "excepto muebles de madera". Si query es "muebles madera", penalizar.
            # Si query es solo "muebles", NO penalizar (porque podría ser muebles de metal).
            # PERO: Si el segmento es solo una palabra "excepto muebles", entonces sí penalizar.
            
            query_words_set = set(palabras_query)
            
            # HEURÍSTICA DE CONTRADICCIÓN:
            # Si el segmento de exclusión está contenido completamente en la parte "positiva" del título,
            # ignorarlo. Esto sucede cuando el título dice "Fabricación de X" y la exclusión dice
            # "Fabricación de X (tipo específico)".
            
            # 1. Obtener parte positiva del título (antes de "excepto")
            # Nota: title_norm ya está normalizado
            positive_title = title_norm.split('excepto')[0]
            positive_title_words = set(p for p in re.findall(r'\w+', positive_title) if len(p) > 2 and p not in stopwords)
            
            # 2. Verificar si el segmento de exclusión es un subset del título positivo
            # Si seg_words es subset de positive_title_words, significa que estamos excluyendo
            # algo que el propio título afirma ser. En este contexto, la exclusión suele ser
            # una refinación ("...de frutas, excepto frutas confitadas") y no una negación total.
            # Por tanto, si la query coincide con el título general, NO debemos penalizar.
            if set(seg_words).issubset(positive_title_words):
                continue

            # Caso especial: Si el segmento tiene 1 sola palabra significativa, penalizar si está en query
            if len(seg_words) == 1:
                if seg_words[0] in query_words_set:
                    score -= 200.0
                    exclusion_hit = segmento.strip()
                    break
            
            # Caso general: Subset match
            # Si el usuario busca "fabricación de muebles de madera" y la exclusión es "muebles de madera", penalizar.
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
        Cada elemento en las listas es un diccionario con:
        - codigo_nace: código NACE encontrado
        - descripcion_nace: descripción truncada del código
        - descripcion_completa: descripción completa del código
        - codigo_iaf: sector IAF al que pertenece
        - nombre_iaf: nombre del sector IAF
        - relevancia: score de relevancia
        - riesgos: lista de riesgos clave del sector
        - razon_exclusion (solo en 'excluded'): el segmento de exclusión que causó la penalización
    """
    # Cargar mapeo si no se proporciona
    if mapping is None:
        if mapping_path is None:
            # Usar el archivo por defecto del paquete
            mapping = load_mapping()
        else:
            # Cargar desde archivo JSON directamente
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

    resultados = []
    excluidos = []  # Candidatos relevantes pero excluidos

    # Combinar campos para la búsqueda
    full_query_text = f"{query} {actividades_reales} {procesos_criticos}".strip()
    query_norm_full = normalizar_texto(full_query_text)
    
    # Detectar intención de la búsqueda
    # Usar texto normalizado para coincidir con las keywords (que no tienen acentos)
    # IMPORTANTE: La intención se deriva PRINCIPALMENTE de la descripción principal (query).
    # Los otros campos son de apoyo, pero no deben cambiar la categoría base (ej: "software" en procesos no hace que sea una empresa de software).
    if query and query.strip():
        query_norm_intent = normalizar_texto(query)
    else:
        query_norm_intent = query_norm_full
    
    intent_manufacturing = any(w in query_norm_intent for w in ['fabricacion', 'fabricación', 'fabrica', 'fábrica', 'produccion', 'producción', 'manufactura', 'elaboracion', 'elaboración', 'confeccion', 'confección'])
    intent_trade = any(w in query_norm_intent for w in ['comercio', 'venta', 'distribucion', 'distribución', 'tienda', 'almacen', 'almacén', 'mayor', 'menor'])

    # Diccionario de sinónimos para expansión de consulta
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
        'reciclaje': 'valorizacion', # NACE usa "valorización" para reciclaje
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
    'cervecerias': 'bares', # Para asociar impresión digital con artes gráficas (IAF 9)
    'notaria': 'notarios',
    'notario': 'notarios',
    'abogado': 'juridicas',
    'abogados': 'juridicas',
    'bufete': 'juridicas',
    'maquinados': 'mecanica',
    'maquinado': 'mecanica',
    'mecanizado': 'mecanica',
    
    # IT / Digital
    'saas': 'informatica',
    'cloud': 'informatica',
    'ecommerce': 'internet', # Maps to 47.91 via 'internet' (usually) or trade logic
    'ciberseguridad': 'informatica',
    'blockchain': 'informatica',
    'bigdata': 'datos',
    'desarrollador': 'programacion',
    'programador': 'programacion',
    
    # Marketing
    'seo': 'publicidad',
    'sem': 'publicidad',
    'community': 'publicidad', # Community manager
    
    # Logística
    'picking': 'almacenamiento',
    'packing': 'envasado',
    'delivery': 'correos', # 53.20 "actividades postales y de correos"
    'rider': 'correos',
    'paqueteria': 'postal',
    'envios': 'postal',
    
    # Construcción
    'pladur': 'revocamiento',
    'drywall': 'revocamiento',
    'albañileria': 'construccion',
    'reformas': 'construccion',
    
    # Energía
    'fotovoltaica': 'electrica',
    'solar': 'electrica',
    'eolica': 'electrica',
    'biomasa': 'electrica',
    'renovables': 'electrica',
    
    # Servicios
    'callcenter': 'llamadas',
    'contactcenter': 'llamadas',
    'coworking': 'inmobiliarias', # 68.20
    
    # Nuevos Sinónimos Globales (Auditoría Completa)
    # IAF 1-3 (Primario/Alimentación)
    'agrotech': 'agricultura',
    'hidroponia': 'cultivos',
    'mineria': 'extraccion',
    'excavacion': 'extraccion',
    'aridos': 'grava',
    'snacks': 'alimenticios',
    'vegan': 'alimenticios',
    'gourmet': 'alimenticios',
    
    # IAF 4-9 (Manufactura Ligera / Papel / Media)
    'moda': 'confeccion',
    'fashion': 'confeccion',
    'ebanisteria': 'muebles',
    'aserradero': 'aserrado',
    'packaging': 'envases',
    'periodismo': 'agencias', # 63.91 Agencias de noticias
    'rotulacion': 'impresion',
    '3d': 'impresion',
    
    # IAF 10-16 (Química / Plástico / Minerales)
    'cosmetica': 'perfumes',
    'perfumeria': 'perfumes',
    'biotech': 'investigacion', # 72.11
    'laboratorio': 'ensayos', # 71.20
    'polimeros': 'plasticos',
    'prefabricados': 'hormigon',
    
    # IAF 17-23 (Metal / Maquinaria / Transporte)
    'cnc': 'mecanica',
    'torneria': 'mecanica',
    'caldereria': 'estructuras',
    'robotica': 'maquinaria',
    'automatizacion': 'maquinaria',
    'chips': 'componentes',
    'sensores': 'instrumentos',
    'astillero': 'barcos',
    'yates': 'barcos',
    'drones': 'aeronautica', # 30.30
    'trenes': 'ferroviario',
    
    # IAF 24-27 (Reciclaje / Energía / Agua)
    'chatarreria': 'residuos', # 38
    'biogas': 'gas',
    'depuradora': 'alcantarillado',
    
    # IAF 28-32 (Construcción / Comercio / Transporte / Finanzas)
    'electricista': 'instalaciones',
    'retail': 'menor', # Comercio al por menor (47)
    'concesionario': 'vehiculos',
    'taller': 'mantenimiento',
    'hosteleria': 'restaurantes',
    'turismo': 'agencias', # Agencias de viaje
    'mudanzas': 'transporte',
    'fintech': 'financieros',
    
    # IAF 33-39 (Servicios Profesionales / Públicos / Sociales)
    'devops': 'informatica',
    'agile': 'consultoria',
    'project': 'consultoria', # Project management
    'facility': 'limpieza', # Facility management (often cleaning/maintenance)
    'ayuntamiento': 'publica',
    'elearning': 'educacion', # 85
    'bootcamp': 'educacion',
    'master': 'educacion',
    'fisioterapia': 'sanitarias',
    'estetica': 'belleza',
    'wellness': 'fisico', # 96.04 Bienestar físico
    'ong': 'asociativas', # 94
    'fundacion': 'asociativas',
    'voluntariado': 'social',
    
    # Decoración / Navidad
    'navidad': 'regalo',
    'navideñas': 'regalo',
    'navidenas': 'regalo',
    'adornos': 'regalo',
    'decoracion': 'regalo',
    
    # Ambigüedad / Otros
    'dolor': 'medicina',
    'universitaria': 'educacion',
    }

    # Expansión de consulta con sinónimos (Usamos query_norm_full para incluir keywords de todos los campos)
    query_words = query_norm_full.split()
    expanded_query_words = []
    for word in query_words:
        expanded_query_words.append(word)
        if word in SYNONYMS:
            expanded_query_words.append(SYNONYMS[word])
    
    # Reconstruir query expandida para el cálculo de relevancia
    expanded_query = " ".join(expanded_query_words)

    # Buscar en todas las descripciones NACE
    for sector in mapping:
        codigo_iaf = sector.get('codigo_iaf')
        nombre_iaf = sector.get('nombre_iaf', '')
        
        # Obtener riesgos del sector
        riesgos_sector = get_risks_for_iaf(codigo_iaf)

        for desc_obj in sector.get('descripcion_nace', []):
            codigo_nace = desc_obj.get('codigo')
            descripcion = desc_obj.get('descripcion', '')

            # Usar la query expandida para el cálculo
            score, base_score, exclusion_hit = calcular_relevancia(expanded_query, descripcion)
            
            if score > 0 or (base_score > 50 and exclusion_hit):
                # Ajuste por intención
                # Extraer división NACE (primeros 2 dígitos)
                try:
                    nace_div = int(codigo_nace.split('.')[0])
                except (ValueError, IndexError):
                    nace_div = 0

                # Lógica de Manufactura (Divisiones 10-33)
                if intent_manufacturing:
                    if 10 <= nace_div <= 33:
                        pass  # No boost global para evitar ruido (confiamos en los pesos específicos)
                    elif 45 <= nace_div <= 47:
                        score -= 200.0  # Penalización fuerte a comercio
                    elif nace_div < 10:
                        score -= 50.0 # Penalización leve a agricultura/minería si se busca fabricación

                # Lógica de Comercio (Divisiones 45-47)
                elif intent_trade:
                    if 45 <= nace_div <= 47:
                        score += 50.0  # Boost comercio (aquí sí tiene sentido ayudar)
                    elif 10 <= nace_div <= 33:
                        score -= 200.0  # Penalización fuerte a manufactura

                # PROTECCIÓN DE CONTEXTO DIGITAL (Global)
                # Si la query tiene intención digital clara, penalizar sectores físicos que usan metáforas
                # Palabras que cambian el contexto físico a digital
                software_keywords = [
                    'software', 'programacion', 'informatica', 'computadora', 'ordenador', 
                    'app', 'web', 'digital', 'datos', 'sistema', 'red', 'servidor', 'cloud', 'nube',
                    'virtual', 'internet', 'online', 'ciber', 'tecnologia'
                ]
                intent_software = any(w in query_norm_intent for w in software_keywords)
                
                if intent_software:
                    # BOOST a sectores IT reales para asegurar que ganen sobre coincidencias parciales
                    # 62: Programación/Consultoría
                    # 63: Servicios de información (Proceso de datos, portales web)
                    # 58.2: Edición de software
                    if nace_div in [62, 63] or codigo_nace.startswith('58.2'):
                        score += 100.0

                    # Si es software, penalizar sectores puramente FÍSICOS que usan terminología similar
                    # 01-03: Agricultura/Pesca (ej: "granja" de servidores)
                    # 05-09: Minería (ej: "minería" de datos)
                    # 10-33: Manufactura (ej: "fábrica" de software, "alimentación" de datos) -> Excepto 26 (Hardware)
                    # 41-43: Construcción (ej: "construcción" de sitios web, "arquitectura" de software)
                    # 49-53: Transporte (ej: "navegación" web, "tráfico" de datos)
                    # 56: Servicios de comidas (ej: "alimentación")
                    # 81: Servicios a edificios (ej: "limpieza" de virus, "mantenimiento" de software vs edificios)
                    
                    is_physical_sector = (
                        (1 <= nace_div <= 3) or
                        (5 <= nace_div <= 9) or
                        (10 <= nace_div <= 33 and nace_div != 26) or
                        (41 <= nace_div <= 43) or
                        (49 <= nace_div <= 53) or
                        (nace_div == 56) or
                        (nace_div == 81) # Limpieza/Jardinería
                    )
                    
                    if is_physical_sector:
                        score -= 200.0

                # PROTECCIÓN DE SERVICIOS PERSONALES (Peluquería vs Corte de piedra/metal)
                intent_personal = any(w in query_norm_intent for w in ['pelo', 'cabello', 'peluqueria', 'estetica', 'belleza', 'manicura'])
                if intent_personal:
                    # Penalizar manufactura y construcción (ej: "corte" de piedra)
                    if (10 <= nace_div <= 33) or (41 <= nace_div <= 43):
                        score -= 200.0

                # PROTECCIÓN MÉDICA (Operación médica vs Operaciones financieras/negocios)
                intent_medical = any(w in query_norm_intent for w in ['medico', 'medica', 'cirugia', 'operacion', 'paciente', 'hospital', 'clinica', 'salud', 'enfermeria', 'dolor'])
                if intent_medical:
                    # Si es contexto médico, penalizar financiero/inmobiliario/negocios (64-70)
                    # "Operación" es muy común en negocios.
                    if 64 <= nace_div <= 70:
                        score -= 200.0
                    # Penalizar también manufactura (salvo farmacéutica 21 y equipos médicos 26/32)
                    if 10 <= nace_div <= 33 and nace_div not in [21, 26, 32]:
                        score -= 50.0

                # PROTECCIÓN DECORACIÓN / NAVIDAD (Esferas navideñas vs Esferas de reloj)
                intent_decoration = any(w in query_norm_intent for w in ['navidad', 'navideñas', 'navidenas', 'adornos', 'decoracion', 'fiesta', 'regalo'])
                if intent_decoration:
                    # Penalizar relojes (26.52) porque "esferas" es un componente de reloj
                    if codigo_nace == '26.52':
                        score -= 200.0
                    # Boost a Otras industrias manufactureras (32.99) que incluye artículos de fiesta/regalo
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
                        'riesgos': riesgos_sector # Adjuntar riesgos
                    })
                elif base_score > 100 and exclusion_hit:
                    # Si tenía buena puntuación base pero fue excluido por una cláusula específica
                    excluidos.append({
                        'codigo_nace': codigo_nace,
                        'descripcion_nace': descripcion[:300] + '...' if len(descripcion) > 300 else descripcion,
                        'descripcion_completa': descripcion,
                        'codigo_iaf': codigo_iaf,
                        'nombre_iaf': nombre_iaf,
                        'relevancia': base_score, # Guardamos el score base para mostrar qué tan relevante era
                        'razon_exclusion': exclusion_hit
                    })

    # Ordenar por relevancia (mayor a menor)
    resultados.sort(key=lambda x: x['relevancia'], reverse=True)
    excluidos.sort(key=lambda x: x['relevancia'], reverse=True)

    # Filtrado Dinámico (Dynamic Thresholding) y Mínimo Absoluto
    MIN_SCORE_THRESHOLD = 20.0  # Umbral mínimo para considerar un resultado válido
    
    if resultados:
        max_score = resultados[0]['relevancia']
        
        # Si el mejor resultado es muy pobre, no devolver nada
        if max_score < MIN_SCORE_THRESHOLD:
            resultados = []
        else:
            threshold = max_score * 0.5
            resultados = [r for r in resultados if r['relevancia'] >= threshold]

    return {
        'results': resultados[:top_n],
        'excluded': excluidos[:3] # Solo mostrar los top 3 excluidos para no saturar
    }
