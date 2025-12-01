# Diccionario de Riesgos Clave por Sector IAF
# Basado en estándares generales de la industria (ISO 9001 / ISO 45001 / ISO 14001)

IAF_RISKS = {
    1: [ # Agricultura, pesca
        "Condiciones climáticas adversas y estacionalidad",
        "Plagas y enfermedades de cultivos/animales",
        "Seguridad alimentaria y trazabilidad",
        "Uso de agroquímicos y gestión de residuos"
    ],
    2: [ # Minería y canteras
        "Seguridad laboral (derrumbes, explosiones)",
        "Impacto ambiental (aguas, suelos)",
        "Cumplimiento normativo estricto",
        "Gestión de residuos peligrosos"
    ],
    3: [ # Productos alimenticios, bebidas y tabaco
        "Contaminación cruzada y alérgenos",
        "Higiene y cadena de frío",
        "Etiquetado y trazabilidad",
        "Caducidad de materias primas"
    ],
    4: [ # Textiles y productos textiles
        "Condiciones laborales en la cadena de suministro",
        "Uso de tintes y químicos peligrosos",
        "Inflamabilidad de materiales",
        "Gestión de residuos textiles"
    ],
    5: [ # Pieles y productos de piel
        "Uso de cromo y químicos en curtido",
        "Impacto ambiental de efluentes",
        "Bienestar animal (trazabilidad)",
        "Calidad y durabilidad del material"
    ],
    6: [ # Maderas y productos de madera
        "Polvo de madera (riesgo respiratorio/explosivo)",
        "Incendios en almacenamiento",
        "Origen sostenible de la madera (FSC/PEFC)",
        "Uso de adhesivos y barnices tóxicos"
    ],
    7: [ # Pulpa, papel y productos de papel
        "Alto consumo de agua y energía",
        "Emisiones atmosféricas y efluentes",
        "Reciclabilidad del producto final",
        "Riesgo de incendio en bobinas"
    ],
    8: [ # Compañías de publicación
        "Propiedad intelectual y derechos de autor",
        "Veracidad de la información (Fake news)",
        "Digitalización y ciberseguridad",
        "Gestión de residuos de tinta/papel"
    ],
    9: [ # Compañías de impresión
        "Manejo de solventes y tintas (COVs)",
        "Residuos peligrosos",
        "Errores en preimpresión y acabados",
        "Plazos de entrega ajustados"
    ],
    10: [ # Fabricación del coque y productos de petróleo refinados
        "Riesgo de explosión e incendio mayor",
        "Derrames y contaminación ambiental",
        "Seguridad de procesos críticos (HAZOP)",
        "Exposición a sustancias cancerígenas"
    ],
    11: [ # Combustible nuclear
        "Radiación y seguridad nuclear",
        "Gestión de residuos radioactivos a largo plazo",
        "Seguridad física y no proliferación",
        "Emergencias radiológicas"
    ],
    12: [ # Químicos, productos químicos y fibras
        "Reacciones químicas descontroladas",
        "Transporte de mercancías peligrosas (ADR)",
        "Exposición laboral a agentes químicos",
        "Cumplimiento REACH y normativas locales"
    ],
    13: [ # Farmacéuticos
        "Contaminación estéril/microbiológica",
        "Cumplimiento GMP (Buenas Prácticas de Manufactura)",
        "Integridad de datos y ensayos clínicos",
        "Falsificación de medicamentos"
    ],
    14: [ # Hule y productos de plástico
        "Emisiones de humos y olores",
        "Gestión de residuos plásticos (microplásticos)",
        "Seguridad en maquinaria (atrapamientos)",
        "Uso de aditivos peligrosos"
    ],
    15: [ # Productos minerales no metálicos
        "Silicosis y polvo en suspensión",
        "Altas temperaturas en hornos",
        "Consumo energético intensivo",
        "Roturas y fragilidad del producto"
    ],
    16: [ # Concreto, cemento, cal, yeso, etc
        "Emisiones de CO2 y polvo",
        "Seguridad en canteras y transporte",
        "Calidad y resistencia del material",
        "Impacto paisajístico"
    ],
    17: [ # Metales básicos y productos de metal fabricados
        "Riesgos térmicos (fundición/soldadura)",
        "Cortes y atrapamientos mecánicos",
        "Emisiones de humos metálicos",
        "Corrosión y fatiga de materiales"
    ],
    18: [ # Maquinaria y equipo
        "Seguridad de máquinas (Marcado CE)",
        "Fallos mecánicos y fiabilidad",
        "Ergonomía en el diseño",
        "Mantenimiento y servicio post-venta"
    ],
    19: [ # Equipo eléctrico y óptico
        "Riesgo eléctrico y compatibilidad electromagnética",
        "Obsolescencia tecnológica rápida",
        "Gestión de residuos electrónicos (RAEE)",
        "Precisión y calibración"
    ],
    20: [ # Construcción naval
        "Trabajos en altura y espacios confinados",
        "Soldadura y oxicorte en entornos cerrados",
        "Cumplimiento de normativas marítimas (IMO)",
        "Impacto ambiental en astilleros"
    ],
    21: [ # Aerospacial
        "Seguridad crítica (fallo catastrófico)",
        "Trazabilidad de componentes",
        "Certificación estricta (AS9100)",
        "Materiales compuestos y nuevos procesos"
    ],
    22: [ # Otro equipo de transporte
        "Seguridad del vehículo y pasajeros",
        "Emisiones y eficiencia energética",
        "Cadena de suministro compleja (JIT)",
        "Defectos de fabricación y llamadas a revisión"
    ],
    23: [ # Fabricación no clasificada en otra parte
        "Variabilidad de procesos y riesgos",
        "Cumplimiento de normativas específicas del producto",
        "Seguridad general en manufactura",
        "Gestión de residuos diversos"
    ],
    24: [ # Reciclado
        "Exposición a agentes biológicos/químicos desconocidos",
        "Incendios en plantas de residuos",
        "Trazabilidad del material recuperado",
        "Cumplimiento normativo ambiental"
    ],
    25: [ # Suministro de electricidad
        "Seguridad de la red y continuidad del servicio",
        "Riesgo eléctrico (alta tensión)",
        "Impacto ambiental de la generación",
        "Ciberseguridad de infraestructuras críticas"
    ],
    26: [ # Suministro de gas
        "Fugas y explosiones",
        "Integridad de ductos y redes",
        "Seguridad en el suministro continuo",
        "Mantenimiento de infraestructuras"
    ],
    27: [ # Suministro de agua
        "Calidad y potabilidad del agua",
        "Gestión de lodos y depuración",
        "Fugas y pérdidas en la red",
        "Seguridad de presas y embalses"
    ],
    28: [ # Construcción
        "Caídas a distinto nivel",
        "Coordinación de seguridad y salud",
        "Gestión de subcontratas",
        "Plazos y costes (desviaciones)"
    ],
    29: [ # Comercio al mayoreo y menudeo
        "Gestión de stock y caducidades",
        "Atención al cliente y reclamaciones",
        "Seguridad en almacenes (carretillas)",
        "Protección de datos de clientes"
    ],
    30: [ # Hoteles y restaurantes
        "Seguridad alimentaria (HACCP)",
        "Higiene y limpieza (Legionella)",
        "Seguridad contra incendios en edificios",
        "Atención al cliente y reputación"
    ],
    31: [ # Transporte, almacenamiento y comunicación
        "Seguridad vial y accidentes",
        "Mantenimiento de flota",
        "Cumplimiento de tiempos de entrega",
        "Pérdida o daño de mercancías"
    ],
    32: [ # Intervención financiera; bienes raíces; alquiler
        "Blanqueo de capitales y fraude",
        "Ciberseguridad y protección de datos",
        "Riesgo de crédito y liquidez",
        "Cumplimiento regulatorio financiero"
    ],
    33: [ # Información tecnológica
        "Ciberseguridad y ransomware",
        "Protección de datos (GDPR/LOPD)",
        "Continuidad del negocio (Disaster Recovery)",
        "Obsolescencia tecnológica"
    ],
    34: [ # Servicios de ingeniería
        "Responsabilidad civil profesional",
        "Errores de cálculo y diseño",
        "Cumplimiento de normativas técnicas",
        "Gestión de proyectos complejos"
    ],
    35: [ # Otros servicios
        "Calidad del servicio prestado",
        "Competencia del personal",
        "Satisfacción del cliente",
        "Cumplimiento de contratos"
    ],
    36: [ # Administración pública
        "Transparencia y anticorrupción",
        "Eficiencia en el gasto público",
        "Protección de datos ciudadanos",
        "Ciberseguridad gubernamental"
    ],
    37: [ # Educación
        "Calidad educativa y competencia docente",
        "Seguridad y protección de menores",
        "Acoso escolar (Bullying)",
        "Adaptación tecnológica"
    ],
    38: [ # Salud y asistencia social
        "Seguridad del paciente (errores médicos)",
        "Infecciones nosocomiales",
        "Protección de datos de salud",
        "Fatiga y estrés del personal"
    ],
    39: [ # Otros servicios sociales
        "Gestión de fondos y donaciones",
        "Protección de colectivos vulnerables",
        "Voluntariado y riesgos laborales",
        "Reputación y confianza pública"
    ]
}

def get_risks_for_iaf(iaf_code):
    """Devuelve la lista de riesgos para un código IAF dado (int o str)."""
    try:
        code = int(iaf_code)
        return IAF_RISKS.get(code, ["Riesgos generales del sector no especificados."])
    except (ValueError, TypeError):
        return ["Código IAF no válido."]
