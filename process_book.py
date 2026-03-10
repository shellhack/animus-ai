"""
ANIMUS Business — Book Processor
Feeds a Spanish PDF book into ANIMUS memory and reports what it learned.
Usage: python process_book.py <book.pdf> [memoria_business.json]
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from pypdf import PdfReader

# ──────────────────────────────────────────────────────────────────────────────
# VOCABULARIO DE NEGOCIACIÓN — extensión del MAPA_ES_TOKEN
# ──────────────────────────────────────────────────────────────────────────────

# Palabras específicas de negociación mapeadas a tokens internos
MAPA_NEGOCIACION = {
    # Problemas / tensiones en negociación
    "conflicto":    "crisis",
    "presión":      "threat",
    "presion":      "threat",
    "obstáculo":    "barrier",
    "obstaculo":    "barrier",
    "fracaso":      "failure",
    "riesgo":       "risk",
    "crisis":       "crisis",
    "amenaza":      "threat",
    "amenazas":     "threat",
    "desacuerdo":   "gap",
    "impasse":      "gap",
    "problema":     "failure",
    "problemas":    "failure",
    "pérdida":      "loss",
    "perdida":      "loss",
    "rechazo":      "failure",
    "deuda":        "debt",
    "déficit":      "deficit",
    "escasez":      "shortage",
    "quiebra":      "bankruptcy",
    "competencia":  "gap",
    # Soluciones / resoluciones en negociación
    "acuerdo":      "solution",
    "trato":        "solution",
    "contrato":     "regulation",
    "oferta":       "initiative",
    "concesión":    "reform",
    "concesion":    "reform",
    "compromiso":   "cooperation",
    "estrategia":   "algorithm",
    "ventaja":      "innovation",
    "solución":     "solution",
    "solucion":     "solution",
    "poder":        "incentive",
    "negociación":  "cooperation",
    "negociacion":  "cooperation",
    "alianza":      "cooperation",
    "coalición":    "coalition",
    "coalicion":    "coalition",
    "inversión":    "incentive",
    "inversion":    "incentive",
    "reforma":      "reform",
    "innovación":   "innovation",
    "innovacion":   "innovation",
    "política":     "policy",
    "politica":     "policy",
    "regulación":   "regulation",
    "regulacion":   "regulation",
    "educación":    "education",
    "educacion":    "education",
    "desarrollo":   "developed",
}

STOPWORDS = {
    "para", "como", "pero", "más", "cuando", "todo", "esta", "este",
    "algo", "bien", "solo", "muy", "cada", "mismo", "puede", "tiene",
    "hace", "dice", "dijo", "años", "entre", "sobre", "desde", "hasta",
    "también", "porque", "había", "estar", "tienen", "hacer", "después",
    "antes", "ahora", "donde", "siempre", "nunca", "quiero", "podría",
}

PALABRAS_TENSION = {
    "conflicto", "presión", "presion", "obstáculo", "obstaculo", "fracaso",
    "riesgo", "crisis", "amenaza", "amenazas", "desacuerdo", "impasse",
    "problema", "problemas", "pérdida", "perdida", "rechazo", "deuda",
    "déficit", "escasez", "quiebra", "competencia",
}

PALABRAS_RESOLUCION = {
    "acuerdo", "trato", "contrato", "oferta", "concesión", "concesion",
    "compromiso", "estrategia", "ventaja", "solución", "solucion",
    "poder", "negociación", "negociacion", "alianza", "coalición",
    "coalicion", "inversión", "inversion", "reforma", "innovación",
    "innovacion", "política", "politica",
}


# ──────────────────────────────────────────────────────────────────────────────
# MEMORY HELPERS
# ──────────────────────────────────────────────────────────────────────────────

TECHO = 100.0

def reforzar(d, clave, valor):
    d[clave] = min(d.get(clave, 0.0) + valor, TECHO)

def traducir(token, lenguaje):
    candidatos = {k: v for k, v in lenguaje.items() if k.endswith(f'__={token}')}
    if not candidatos:
        return token
    return max(candidatos.items(), key=lambda x: x[1])[0].split('__=')[0]


# ──────────────────────────────────────────────────────────────────────────────
# BOOK PROCESSOR
# ──────────────────────────────────────────────────────────────────────────────

def procesar_libro(pdf_path, memoria):
    reader = PdfReader(pdf_path)
    paginas_procesadas = 0
    nuevas_conexiones = 0
    nuevas_palabras = 0

    todos_problemas = set(k.split('_')[-1] for k in memoria['problemas'])
    todos_soluciones = set(k.split('_')[-1] for k in memoria['soluciones'])

    print(f"\n📖 Procesando: {Path(pdf_path).name}")
    print(f"   Páginas: {len(reader.pages)}")
    print(f"   Memoria actual: {len(memoria['conexiones'])} conexiones\n")

    for i, page in enumerate(reader.pages):
        texto = page.extract_text()
        if not texto or len(texto.strip()) < 50:
            continue

        palabras = re.findall(r'[a-z\xe1\xe9\xed\xf3\xfa\xfc\xf1]{4,}', texto.lower())
        palabras_set = set(p for p in palabras if p not in STOPWORDS)

        # 1. Detectar tensiones y resoluciones en esta página
        tensiones = [p for p in palabras_set if p in PALABRAS_TENSION]
        resoluciones = [p for p in palabras_set if p in PALABRAS_RESOLUCION]

        # 2. Reforzar memoria de problemas y soluciones
        for p in tensiones:
            if p in MAPA_NEGOCIACION:
                token = MAPA_NEGOCIACION[p]
                clave = f"libro_negociacion_{token}"
                reforzar(memoria['problemas'], clave, 1.5)
                todos_problemas.add(token)

        for r in resoluciones:
            if r in MAPA_NEGOCIACION:
                token = MAPA_NEGOCIACION[r]
                clave = f"libro_negociacion_{token}"
                reforzar(memoria['soluciones'], clave, 1.5)
                todos_soluciones.add(token)

        # 3. Detectar conexiones — páginas con AMBOS tensión y resolución
        if tensiones and resoluciones:
            for t in tensiones[:3]:
                for r in resoluciones[:3]:
                    if t in MAPA_NEGOCIACION and r in MAPA_NEGOCIACION:
                        token_t = MAPA_NEGOCIACION[t]
                        token_r = MAPA_NEGOCIACION[r]
                        clave = f"libro_negociacion_{token_t}__>libro_negociacion_{token_r}"
                        es_nueva = clave not in memoria['conexiones']
                        reforzar(memoria['conexiones'], clave, 0.8)
                        if es_nueva:
                            nuevas_conexiones += 1

        # 4. Aprendizaje de lenguaje — reforzar vocabulario español
        for palabra in palabras_set:
            if palabra in MAPA_NEGOCIACION:
                token = MAPA_NEGOCIACION[palabra]
                if token in todos_problemas or token in todos_soluciones:
                    conocimiento = sum(
                        v for k, v in memoria['problemas'].items() if k.endswith(f'_{token}')
                    ) + sum(
                        v for k, v in memoria['soluciones'].items() if k.endswith(f'_{token}')
                    )
                    if conocimiento > 0:
                        clave_lang = f"{palabra}__={token}"
                        es_nueva = clave_lang not in memoria['lenguaje']
                        fuerza = min(conocimiento / 20.0, 3.0)
                        reforzar(memoria['lenguaje'], clave_lang, fuerza)
                        if es_nueva:
                            nuevas_palabras += 1

        paginas_procesadas += 1

        if (i + 1) % 50 == 0:
            print(f"   [{i+1}/{len(reader.pages)}] Conexiones nuevas: {nuevas_conexiones} | "
                  f"Palabras nuevas: {nuevas_palabras}")

    return paginas_procesadas, nuevas_conexiones, nuevas_palabras


# ──────────────────────────────────────────────────────────────────────────────
# COMPARISON REPORT
# ──────────────────────────────────────────────────────────────────────────────

def comparar_conexiones(memoria):
    """
    Compara conexiones del libro con conexiones previas del agente.
    Detecta convergencias y divergencias.
    """
    conexiones_libro = {k: v for k, v in memoria['conexiones'].items()
                       if k.startswith('libro_negociacion_')}
    conexiones_web = {k: v for k, v in memoria['conexiones'].items()
                     if not k.startswith('libro_negociacion_')}

    lenguaje = memoria['lenguaje']

    print("\n" + "="*65)
    print("  ANÁLISIS COMPARATIVO — Libro vs. Fuentes Web")
    print("="*65)

    print(f"\n  Conexiones del libro: {len(conexiones_libro)}")
    print(f"  Conexiones de fuentes web: {len(conexiones_web)}")

    # Top conexiones del libro
    print("\n  Top conexiones detectadas en el libro:")
    for k, v in sorted(conexiones_libro.items(), key=lambda x: -x[1])[:8]:
        partes = k.split('__>')
        if len(partes) == 2:
            token_p = partes[0].split('_')[-1]
            token_s = partes[1].split('_')[-1]
            word_p = traducir(token_p, lenguaje)
            word_s = traducir(token_s, lenguaje)
            print(f"    📖 {word_p} → {word_s}: {v:.1f}")

    # Buscar convergencias — mismos tokens en libro Y fuentes web
    tokens_libro = set()
    for k in conexiones_libro:
        partes = k.split('__>')
        if len(partes) == 2:
            tokens_libro.add(partes[0].split('_')[-1])
            tokens_libro.add(partes[1].split('_')[-1])

    tokens_web = set()
    for k in conexiones_web:
        partes = k.split('__>')
        if len(partes) == 2:
            tokens_web.add(partes[0].split('_')[-1])
            tokens_web.add(partes[1].split('_')[-1])

    convergencias = tokens_libro & tokens_web
    solo_libro = tokens_libro - tokens_web
    solo_web = tokens_web - tokens_libro

    print(f"\n  Conceptos compartidos (libro + web): {len(convergencias)}")
    if convergencias:
        words = [traducir(t, lenguaje) for t in list(convergencias)[:8]]
        print(f"    {', '.join(words)}")

    print(f"\n  Conceptos únicos del libro: {len(solo_libro)}")
    if solo_libro:
        words = [traducir(t, lenguaje) for t in list(solo_libro)[:8]]
        print(f"    {', '.join(words)}")

    print(f"\n  Conceptos únicos de la web: {len(solo_web)}")
    if solo_web:
        words = [traducir(t, lenguaje) for t in list(solo_web)[:5]]
        print(f"    {', '.join(words)}")

    print("\n  Vocabulario en español después del libro:")
    print(f"    Total palabras: {len(lenguaje)}")
    nuevas_negociacion = [k.split('__=')[0] for k in lenguaje
                         if k.split('__=')[0] in MAPA_NEGOCIACION]
    print(f"    Palabras de negociación: {len(set(nuevas_negociacion))}")
    if nuevas_negociacion:
        print(f"    Muestra: {', '.join(sorted(set(nuevas_negociacion))[:10])}")

    print("="*65)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python process_book.py <libro.pdf> [memoria_business.json]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    memoria_path = sys.argv[2] if len(sys.argv) > 2 else "memoria_business.json"

    if not Path(pdf_path).exists():
        print(f"Error: {pdf_path} no encontrado.")
        sys.exit(1)

    if not Path(memoria_path).exists():
        print(f"Error: {memoria_path} no encontrado.")
        sys.exit(1)

    # Cargar memoria
    with open(memoria_path, encoding='utf-8') as f:
        memoria = json.load(f)

    # Convertir a defaultdict para compatibilidad
    memoria['problemas'] = dict(memoria.get('problemas', {}))
    memoria['soluciones'] = dict(memoria.get('soluciones', {}))
    memoria['conexiones'] = dict(memoria.get('conexiones', {}))
    memoria['lenguaje'] = dict(memoria.get('lenguaje', {}))

    # Procesar libro
    paginas, nuevas_conn, nuevas_words = procesar_libro(pdf_path, memoria)

    print(f"\n✅ Libro procesado:")
    print(f"   Páginas leídas: {paginas}")
    print(f"   Conexiones nuevas: {nuevas_conn}")
    print(f"   Palabras nuevas en vocabulario: {nuevas_words}")

    # Análisis comparativo
    comparar_conexiones(memoria)

    # Guardar memoria actualizada
    memoria['ultima_actualizacion'] = datetime.now().isoformat()
    with open(memoria_path, 'w', encoding='utf-8') as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Memoria actualizada: {memoria_path}")
    print(f"   Total conexiones ahora: {len(memoria['conexiones'])}")
