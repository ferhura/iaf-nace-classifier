import fitz  # PyMuPDF
import json
import re
from typing import Dict, List, Tuple

PDF_PATH = "Codigo_NACE_sectoresema.pdf"
# Archivo de salida principal con mapeo IAF→NACE expandido y descripciones completas
OUTPUT_JSON = "iaf_nace_mapeo_expandido.json"


# Utilidades de normalización para mitigar errores comunes de OCR
def _norm_text(s: str) -> str:
    s = s.replace("\u2013", "-")  # en-dash → hyphen
    s = s.replace("\u2014", "-")  # em-dash → hyphen
    s = s.replace("except0", "excepto")  # cero → o
    s = s.replace("Except0", "Excepto")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# Inicio de sector IAF: 1-2 dígitos al comienzo NO seguidos de '.' inmediatamente
IAF_START_RE = re.compile(r"^\s*(?P<codigo>\d{1,2})(?!\.)\b[ \t:]+(?!excepto\b)(?P<rest>.*)$", re.IGNORECASE)
NACE_CODE_RE = re.compile(r"\b(\d{2}(?:\.\d{1,2})?)\b")
EXCEPTO_RE = re.compile(r"\bexcepto\b", re.IGNORECASE)



def _split_nombre_y_codigos(texto: str) -> Tuple[str, str]:
    """Divide en nombre IAF y segmento de códigos+exclusiones.

    Estrategia: buscar la primera aparición de un código NACE; todo lo previo es el nombre.
    """
    m = NACE_CODE_RE.search(texto)
    if not m:
        return texto.strip(), ""
    idx = m.start()
    nombre = texto[:idx].strip(" ;,.- ")
    resto = texto[idx:].strip()
    return nombre, resto


def _parse_codigos_y_exclusiones(segmento: str) -> Tuple[List[str], List[str]]:
    if not segmento:
        return [], []
    segmento = _norm_text(segmento)

    # Separar en dos partes: antes y después de "excepto"
    m = EXCEPTO_RE.search(segmento)
    if m:
        antes = segmento[: m.start()]
        despues = segmento[m.end() :]
    else:
        antes = segmento
        despues = ""

    codigos = NACE_CODE_RE.findall(antes)
    exclusiones = NACE_CODE_RE.findall(despues)

    # Normalizar y desduplicar manteniendo orden
    def _dedup(seq: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return _dedup(codigos), _dedup(exclusiones)


def extraer_iaf_nace_desde_pdf():
    doc = fitz.open(PDF_PATH)
    sectores: List[dict] = []
    warnings: List[str] = []

    # Usar palabras para reconstruir líneas y alinear columnas por coordenada Y
    page = doc[0]
    words = page.get_text("words") or []
    # words: (x0, y0, x1, y1, word, block_no, line_no, word_no)
    words.sort(key=lambda w: (round(w[1], 1), w[0]))

    # Agrupar en líneas por proximidad vertical
    lines: List[Tuple[float, str]] = []  # (y, text)
    cur_y = None
    cur_words: List[Tuple[float, str]] = []  # (x, word)
    Y_TOL = 1.5

    for x0, y0, x1, y1, wtxt, *_ in words:
        if cur_y is None or abs(y0 - cur_y) <= Y_TOL:
            cur_y = y0 if cur_y is None else cur_y
            cur_words.append((x0, wtxt))
        else:
            # flush line
            cur_words.sort(key=lambda t: t[0])
            text_line = _norm_text(" ".join(t[1] for t in cur_words))
            if text_line:
                lines.append((cur_y, text_line))
            # start new line
            cur_y = y0
            cur_words = [(x0, wtxt)]
    # flush last line
    if cur_words:
        cur_words.sort(key=lambda t: t[0])
        text_line = _norm_text(" ".join(t[1] for t in cur_words))
        if text_line:
            lines.append((cur_y, text_line))

    # Separar líneas de encabezado, de sectores y de códigos
    sector_lines: List[Tuple[float, int, str]] = []  # (y, iaf, nombre/fragmentos)
    code_lines: List[Tuple[float, str]] = []  # (y, text)

    pending: Tuple[float, int, str] | None = None

    for y, line in lines:
        # Omitir encabezados obvios
        if "DESCRIPCIÓN" in line.upper() and "CÓDIGO" in line.upper():
            continue
        if "NACE" in line and "Rev" in line:
            continue

        m = IAF_START_RE.match(line)
        if m:
            # Cerrar sector pendiente si existía
            if pending is not None:
                sector_lines.append(pending)
                pending = None
            try:
                iaf = int(m.group("codigo"))
            except ValueError:
                continue
            if not (1 <= iaf <= 40):
                continue
            rest = m.group("rest").strip()
            pending = (y, iaf, rest)
            continue

        # Columna de códigos
        if NACE_CODE_RE.search(line) and ("," in line or "excepto" in line.lower()):
            code_lines.append((y, line))
            continue

        # Línea de continuación del nombre del sector
        if pending is not None:
            py, piaf, prest = pending
            prest = (prest + " " + line).strip()
            pending = (py, piaf, prest)
            continue

    if pending is not None:
        sector_lines.append(pending)

    # Alinear cada sector con la línea de códigos más cercana en Y
    used_codes_idx: set[int] = set()
    for y, iaf, rest in sector_lines:
        # encontrar código más cercano en Y
        best_idx = None
        best_dy = None
        for idx, (yc, code_text) in enumerate(code_lines):
            if idx in used_codes_idx:
                continue
            dy = abs(yc - y)
            if best_dy is None or dy < best_dy:
                best_dy = dy
                best_idx = idx

        nombre, segmento = _split_nombre_y_codigos(rest)
        codigos: List[str] = []
        exclusiones: List[str] = []

        # Intentar extraer primero del propio renglón
        c0, e0 = _parse_codigos_y_exclusiones(segmento)
        if c0:
            codigos.extend(c0)
            exclusiones.extend(e0)
            best_idx = None  # no buscar columna de códigos si ya hay

        # Recoger códigos cercanos por coordenada Y (alineación de columnas)
        near_idxs = [
            idx for idx, (yc, _t) in enumerate(code_lines)
            if idx not in used_codes_idx and abs(yc - y) <= 8.0
        ]
        if near_idxs:
            near_idxs.sort(key=lambda i: abs(code_lines[i][0] - y))
            for idx in near_idxs:
                used_codes_idx.add(idx)
                code_text = code_lines[idx][1]
                name2, seg2 = _split_nombre_y_codigos(code_text)
                if name2 and not name2.lower().startswith("no.") and not NACE_CODE_RE.search(name2):
                    nombre = (name2 + " " + nombre).strip()
                c, e = _parse_codigos_y_exclusiones(seg2 if seg2 else code_text)
                codigos.extend(c)
                exclusiones.extend(e)
        elif best_idx is not None and best_dy is not None and best_dy <= 14.0:
            used_codes_idx.add(best_idx)
            code_text = code_lines[best_idx][1]
            name2, seg2 = _split_nombre_y_codigos(code_text)
            if name2 and not name2.lower().startswith("no.") and not NACE_CODE_RE.search(name2):
                nombre = (name2 + " " + nombre).strip()
            c, e = _parse_codigos_y_exclusiones(seg2 if seg2 else code_text)
            codigos.extend(c)
            exclusiones.extend(e)

        if not codigos:
            warnings.append(f"IAF {iaf}: sin códigos NACE detectados (yΔ={best_dy!s}). Nombre='{nombre}'")
        if nombre.lower() == "excepto" or not nombre:
            warnings.append(f"IAF {iaf}: nombre sospechoso '{nombre}'. Revisar OCR/segmentación.")

        sectores.append(
            {
                "codigo_iaf": iaf,
                "nombre_iaf": nombre,
                "codigos_nace": codigos,
                "exclusiones": exclusiones,
                "descripcion_nace": [],
            }
        )

    if warnings:
        print("Advertencias del extractor (revise el PDF si es necesario):")
        for w in warnings:
            print(f" - {w}")

    return sectores


def guardar_json(data):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_nace_code(code: str) -> str:
    code = code.strip()
    m = re.match(r"^(\d{1,2})(?:\.(\d{1,2}))?$", code)
    if not m:
        return code
    major = f"{int(m.group(1)):02d}"
    minor = m.group(2)
    if minor is None:
        return major
    return f"{major}.{int(minor):02d}" if len(minor) == 2 or minor == "00" else f"{major}.{int(minor)}"


def _extraer_descripciones(pdf_path: str) -> Dict[str, str]:
    """Extrae títulos y CUERPOS completos para todos los niveles NACE.

    Detecta encabezados "NN Título" y "NN.N Título" y captura el texto
    subsiguiente (párrafos y viñetas) hasta el próximo encabezado válido.
    Devuelve dict { codigo_nace -> texto_completo }.
    """
    doc = fitz.open(pdf_path)
    desc: Dict[str, str] = {}
    HEAD_RE = re.compile(r"^\s*(\d{2}(?:\.\d{1,2})?)\s+(.+?)\s*$")

    current_code: str | None = None
    buffer_lines: List[str] = []

    def flush():
        nonlocal current_code, buffer_lines
        if current_code is None:
            return
        text = "\n".join(buffer_lines).strip()
        if text:
            desc[current_code] = text
        current_code = None
        buffer_lines = []

    for i in range(1, doc.page_count):
        page = doc[i]
        words = page.get_text("words") or []
        words.sort(key=lambda w: (round(w[1], 1), w[0]))
        Y_TOL = 1.5
        lines: List[Tuple[float, str]] = []
        cur_y = None
        cur_words: List[Tuple[float, str]] = []
        for x0, y0, x1, y1, wtxt, *_ in words:
            if cur_y is None or abs(y0 - cur_y) <= Y_TOL:
                cur_y = y0 if cur_y is None else cur_y
                cur_words.append((x0, wtxt))
            else:
                cur_words.sort(key=lambda t: t[0])
                text_line = _norm_text(" ".join(t[1] for t in cur_words))
                if text_line:
                    lines.append((cur_y, text_line))
                cur_y = y0
                cur_words = [(x0, wtxt)]
        if cur_words:
            cur_words.sort(key=lambda t: t[0])
            text_line = _norm_text(" ".join(t[1] for t in cur_words))
            if text_line:
                lines.append((cur_y, text_line))

        for _y, raw in lines:
            line = raw
            u = line.upper()
            # Saltar cabeceras/footers
            if "NACE REV" in u or "ESTRUCTURA" in u or re.search(r"\d+\s*/\s*\d+", line):
                continue
            # Si es encabezado de código, cerrar el anterior y abrir nuevo
            m = HEAD_RE.match(line)
            if m:
                flush()
                code = _normalize_nace_code(m.group(1))
                title = m.group(2).strip()
                if len(title) < 2:
                    continue
                current_code = code
                buffer_lines.append(f"{code} {title}")
                continue
            # Acumular contenido del código actual
            if current_code is not None:
                buffer_lines.append(line)

    flush()
    return desc


def _expandir_codigos(codigos: List[str], exclusiones: List[str], desc_map: Dict[str, str]) -> List[str]:
    # Normalizar patrones (e.g., "1" -> "01")
    pats = [_normalize_nace_code(c) for c in codigos]
    exps = [_normalize_nace_code(e) for e in exclusiones]

    def excluded(c: str) -> bool:
        for e in exps:
            if c.startswith(e):
                return True
        return False

    # Recolectar todas las descripciones cuyo código coincida por prefijo
    out: List[str] = []
    for p in pats:
        for k in desc_map.keys():
            if k.startswith(p) and not excluded(k):
                out.append(k)

    # Desduplicar manteniendo orden natural
    seen = set()
    unique: List[str] = []
    for c in out:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    def sort_key(c: str):
        if "." in c:
            a, b = c.split(".", 1)
            return (int(a), int(b))
        return (int(c), -1)

    unique.sort(key=sort_key)
    return unique


def _escribir_log_validacion(sectores: List[dict], desc_map: Dict[str, str], warnings: List[str]) -> None:
    total_codigos = 0
    con_desc = 0
    faltantes: List[str] = []
    total_expand = 0
    for s in sectores:
        base = s.get("codigos_nace", [])
        exc = s.get("exclusiones", [])
        for c in base:
            total_codigos += 1
            if c in desc_map:
                con_desc += 1
            else:
                faltantes.append(f"IAF {s.get('codigo_iaf')}: {c}")
        expanded = _expandir_codigos(base, exc, desc_map)
        total_expand += len(expanded)

    lines: List[str] = []
    lines.append("Validación del extractor IAF–NACE")
    lines.append("")
    lines.append(f"Sectores extraídos: {len(sectores)}")
    lines.append(f"Códigos NACE referenciados (sin expandir): {total_codigos}")
    lines.append(f"Códigos con descripción (sin expandir): {con_desc}")
    lines.append(f"Códigos sin descripción (sin expandir): {total_codigos - con_desc}")
    lines.append(f"Total de códigos descritos tras expansión: {total_expand}")
    lines.append("")
    if warnings:
        lines.append("Advertencias:")
        for w in warnings:
            lines.append(f" - {w}")
        lines.append("")
    if faltantes:
        lines.append("Códigos NACE sin descripción mapeada:")
        for f in faltantes:
            lines.append(f" - {f}")

    with open("extract_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    print("Procesando PDF…")
    sectores = extraer_iaf_nace_desde_pdf()

    # Extraer descripciones de NACE desde páginas 2..N
    desc_map = _extraer_descripciones(PDF_PATH)

    # Rellenar descripcion_nace en cada sector, expandiendo a todos los niveles
    warnings: List[str] = []
    for s in sectores:
        expanded = _expandir_codigos(s.get("codigos_nace", []), s.get("exclusiones", []), desc_map)
        desclist = [{"codigo": c, "descripcion": desc_map[c]} for c in expanded if c in desc_map]
        s["descripcion_nace"] = desclist

    # Escribir log de validación
    _escribir_log_validacion(sectores, desc_map, warnings)

    guardar_json(sectores)
    print(f"\u2705 JSON generado en {OUTPUT_JSON} con {len(sectores)} sectores IAF procesados.")


if __name__ == "__main__":
    main()
