"""
ANIMUS — Universal Wisdom & Tech Book Processor
Processes any PDF and feeds patterns into ANIMUS memory.
Supports: philosophy, wisdom literature, technology, AI/ML books.

Usage:
    python process_book_v2.py <book.pdf> [memoria.json] [--tipo wisdom|tech|auto]

Examples:
    python process_book_v2.py meditaciones.pdf memoria_business.json
    python process_book_v2.py deep_learning.pdf memoria_business.json --tipo tech
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from pypdf import PdfReader
import unicodedata

# ──────────────────────────────────────────────────────────────────────────────
# VOCABULARY MAPS
# ──────────────────────────────────────────────────────────────────────────────

# WISDOM — philosophy, stoicism, strategy, taoism
MAPA_SABIDURIA = {
    # Tensiones / desequilibrios
    "orgullo":        "failure",      "soberbia":       "failure",
    "necedad":        "failure",      "necio":          "failure",
    "ignorancia":     "failure",      "error":          "failure",
    "vicio":          "failure",      "debilidad":      "failure",
    "pereza":         "poverty",      "perezoso":       "poverty",
    "mentira":        "corruption",   "engaño":         "fraud",
    "codicia":        "gap",          "avaricia":       "gap",
    "ira":            "crisis",       "cólera":         "crisis",
    "violencia":      "collapse",     "guerra":         "crisis",
    "conflicto":      "crisis",       "enemigo":        "threat",
    "derrota":        "failure",      "rendición":      "failure",
    "miedo":          "threat",       "temor":          "threat",
    "dolor":          "crisis",       "sufrimiento":    "crisis",
    "muerte":         "collapse",     "decadencia":     "collapse",
    "desorden":       "crisis",       "caos":           "collapse",
    "debilidad":      "vulnerability","obstáculo":      "failure",
    "obstaculo":      "failure",      "perturbación":   "disruption",
    "perturbacion":   "disruption",   "distracción":    "failure",
    "distraccion":    "failure",      "pasión":         "crisis",
    "passion":        "crisis",       "apego":          "failure",
    "vanidad":        "failure",      "orgullo":        "failure",
    "pobreza":        "poverty",      "miseria":        "poverty",
    "injusticia":     "inequality",   "opresión":       "inequality",
    "opresion":       "inequality",   "tiranía":        "collapse",
    "tirania":        "collapse",
    # Resoluciones / contrapesos
    "sabiduría":      "education",    "sabiduria":      "education",
    "razón":          "algorithm",    "razon":          "algorithm",
    "virtud":         "reform",       "virtudes":       "reform",
    "disciplina":     "developed",    "templanza":      "regulation",
    "fortaleza":      "developed",    "prudencia":      "algorithm",
    "justicia":       "reform",       "justo":          "reform",
    "valor":          "incentive",    "valentía":       "incentive",
    "valentia":       "incentive",    "coraje":         "incentive",
    "humildad":       "cooperation",  "serenidad":      "solution",
    "ecuanimidad":    "solution",     "paciencia":      "prevention",
    "aceptación":     "solution",     "aceptacion":     "solution",
    "meditación":     "algorithm",    "meditacion":     "algorithm",
    "reflexión":      "discovered",   "reflexion":      "discovered",
    "conocimiento":   "discovered",   "aprendizaje":    "education",
    "entendimiento":  "education",    "inteligencia":   "algorithm",
    "estrategia":     "algorithm",    "táctica":        "algorithm",
    "tactica":        "algorithm",    "adaptación":     "transformed",
    "adaptacion":     "transformed",  "flexibilidad":   "transformed",
    "equilibrio":     "solution",     "armonía":        "cooperation",
    "armonia":        "cooperation",  "unidad":         "cooperation",
    "naturaleza":     "renewable",    "orden":          "regulation",
    "ley":            "regulation",   "principio":      "regulation",
    "principios":     "regulation",   "deber":          "regulation",
    "rectitud":       "reform",       "integridad":     "regulation",
    "silencio":       "solution",     "acción":         "developed",
    "accion":         "developed",    "servicio":       "cooperation",
    "liderazgo":      "cooperation",  "maestría":       "developed",
    "maestria":       "developed",    "excelencia":     "developed",
    "perseverancia":  "developed",    "constancia":     "developed",
    "control":        "regulation",   "autocontrol":    "regulation",
    #NUEVOS TOKENS DE ANTROPOLOGÍA ECONÓMICA (Graeber/Diamond)
    "deuda":          "debt",         "credito":        "incentive",
    "dinero":         "algorithm",    "moneda":         "algorithm",
    "trueque":        "gap",          "intercambio":    "cooperation",
    "jerarquia":      "monopoly",     "obligacion":     "debt",
    "esclavo":        "poverty",      "violencia":      "collapse",
    "historia":       "developed",    "mercado":        "regulation",
    "interes":        "gap",          "usura":          "corruption",
}

# TECHNOLOGY — computers, AI, hardware, algorithms
MAPA_TECH = {
    # Hardware tensions
    "cuello de botella":  "bottleneck",  "sobrecalentamiento": "burnout",
    "fallo":              "failure",     "falla":              "failure",
    "error":              "failure",     "bug":                "failure",
    "colapso":            "collapse",    "crash":              "collapse",
    "obsolescencia":      "obsolescence","lentitud":           "gap",
    "latencia":           "gap",         "cuello":             "bottleneck",
    "limitación":         "limitation",  "limitacion":         "limitation",
    "capacidad":          "shortage",    "memoria insuficiente":"shortage",
    "sobrecarga":         "burnout",     "congestión":         "crisis",
    "congestion":         "crisis",      "vulnerabilidad":     "vulnerability",
    "brecha":             "gap",         "fragmentación":      "gap",
    "fragmentacion":      "gap",
    # Hardware solutions
    "procesador":         "algorithm",   "microprocesador":    "algorithm",
    "memoria":            "developed",   "almacenamiento":     "developed",
    "caché":              "solution",    "cache":              "solution",
    "paralelización":     "automation",  "paralelizacion":     "automation",
    "optimización":       "optimized",   "optimizacion":       "optimized",
    "aceleración":        "developed",   "aceleracion":        "developed",
    "compresión":         "solution",    "compresion":         "solution",
    "escalabilidad":      "scaled",      "redundancia":        "prevention",
    "arquitectura":       "framework",   "transistor":         "innovation",
    "circuito":           "algorithm",   "chip":               "innovation",
    "semiconductor":      "innovation",  "quantum":            "innovation",
    "fotónico":           "innovation",  "fotonico":           "innovation",
    # AI/ML tensions
    "sobreajuste":        "failure",     "underfitting":       "failure",
    "sesgo":              "inequality",  "bias":               "inequality",
    "alucinación":        "fraud",       "alucinacion":        "fraud",
    "opacidad":           "corruption",  "caja negra":         "corruption",
    "dependencia":        "addiction",   "desequilibrio":      "gap",
    # AI/ML solutions
    "red neuronal":       "neural",      "neuronal":           "neural",
    "aprendizaje":        "education",   "entrenamiento":      "training",
    "gradiente":          "algorithm",   "retropropagación":   "algorithm",
    "retropropagacion":   "algorithm",   "transformer":        "innovation",
    "atención":           "algorithm",   "atencion":           "algorithm",
    "embeddings":         "algorithm",   "vectores":           "algorithm",
    "parámetros":         "algorithm",   "parametros":         "algorithm",
    "pesos":              "algorithm",   "modelo":             "modeled",
    "modelos":            "modeled",     "inferencia":         "algorithm",
    "datos":              "algorithm",   "dataset":            "algorithm",
    "corpus":             "education",   "tokens":             "algorithm",
    "regularización":     "regulation",  "regularizacion":     "regulation",
    "dropout":            "prevention",  "normalización":      "regulation",
    "normalizacion":      "regulation",  "función de pérdida": "loss",
    "backpropagation":    "algorithm",   "epochs":             "training",
    "batch":              "algorithm",   "hiperparámetros":    "algorithm",
    "hiperparametros":    "algorithm",   "fine-tuning":        "transformed",
    "transfer learning":  "education",   "autoregresivo":      "algorithm",
    # Self-improvement concepts — KEY for ANIMUS self-awareness
    "autoaprendizaje":    "education",   "autoorganización":   "cooperation",
    "autoorganizacion":   "cooperation", "emergencia":         "innovation",
    "emergente":          "innovation",  "adaptativo":         "transformed",
    "recursivo":          "algorithm",   "retroalimentación":  "algorithm",
    "retroalimentacion":  "algorithm",   "metacognición":      "discovered",
    "metacognicion":      "discovered",  "autoconciencia":     "discovered",
    "reflexivo":          "discovered",  "autorreferencial":   "discovered",
    "evolución":          "developed",   "evolucion":          "developed",
    "mutación":           "transformed", "mutacion":           "transformed",
    "selección":          "algorithm",   "seleccion":          "algorithm",
    "fitness":            "developed",   "generación":         "developed",
    "generacion":         "developed",   "mejora":             "developed",
    "mejoras":            "developed",   "actualización":      "transformed",
    "actualizacion":      "transformed", "versión":            "transformed",
    "version":            "transformed", "iteración":          "algorithm",
    "iteracion":          "algorithm",
}

STOPWORDS = {
    "para", "como", "pero", "más", "cuando", "todo", "esta", "este",
    "algo", "bien", "solo", "muy", "cada", "mismo", "puede", "tiene",
    "dice", "dijo", "años", "entre", "sobre", "desde", "hasta", "también",
    "porque", "había", "estar", "tienen", "hacer", "después", "antes",
    "ahora", "donde", "siempre", "nunca", "libro", "capítulo", "capitulo",
    "página", "pagina", "parte", "texto", "autor", "obra", "edición",
    "será", "serán", "hijo", "hijos", "padre", "casa", "alma", "boca",
    "mano", "manos", "ojos", "corazón", "días", "tiempo", "hombre",
    "hombres", "mujer", "pueblo", "tierra", "cosa", "cosas", "manera",
    "forma", "modo", "tipo", "gran", "grande", "pequeño", "nuevo",
    "primera", "segundo", "tercero", "según", "segun", "siendo",
}

TECHO = 100.0


def reforzar(d, clave, valor):
    """
    D05: Refuerzo Logarítmico Autónomo. 
    Sustituye el techo lineal por rendimientos decrecientes.
    """
    import math
    valor_actual = d.get(clave, 0.0)
    # Factor de atenuación: a mayor peso, menor impacto del nuevo dato
    atenuacion = 1 / (1 + math.log1p(valor_actual))
    nuevo_total = valor_actual + (valor * atenuacion)
    d[clave] = round(nuevo_total, 4)


def traducir(token, lenguaje):
    candidatos = {k: v for k, v in lenguaje.items() if k.endswith(f"__={token}")}
    if not candidatos:
        return token
    return max(candidatos.items(), key=lambda x: x[1])[0].split("__=")[0]


def detectar_tipo(texto_muestra):
    """Auto-detect book type from sample text."""
    palabras_tech = sum(1 for p in ["procesador", "algoritmo", "memoria", "red", "datos",
                                     "neural", "aprendizaje automático", "código", "sistema"]
                        if p in texto_muestra.lower())
    palabras_wisdom = sum(1 for p in ["virtud", "alma", "razón", "naturaleza", "deber",
                                       "sabiduría", "filosofía", "estoico", "dao", "tao"]
                          if p in texto_muestra.lower())
    return "tech" if palabras_tech > palabras_wisdom else "wisdom"

def normalizar_token(t):
    # Convierte a minúsculas y elimina tildes
    t = t.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                    if unicodedata.category(c) != 'Mn')

def detectar_contradicciones(texto, mapa, palabras_tension, palabras_resolucion):
    """
    Analiza frases donde una solución (ej. algoritmo) aparece junto a una tensión 
    (ej. corrupción), sugiriendo que la solución podría estar comprometida.
    """
    alertas = []
    # Dividimos por frases para un contexto más preciso
    frases = re.split(r'[.!?]', texto.lower())
    
    for frase in frases:
        palabras = re.findall(r'\b\w+\b', frase)
        p_en_frase = [normalizar_token(p) for p in palabras]
        
        t_encontradas = [p for p in p_en_frase if p in palabras_tension]
        r_encontradas = [p for p in p_en_frase if p in palabras_resolucion]
        
        if t_encontradas and r_encontradas:
            for res in r_encontradas:
                token_res = mapa[res]
                # Si la resolución es un algoritmo o regulación y hay una tensión cerca
                if token_res in ["algorithm", "regulation", "framework"]:
                    for ten in t_encontradas:
                        alertas.append(f"CONTRADICCIÓN: {token_res} vinculado a {mapa[ten]} en: '{frase.strip()[:60]}...'")
    return alertas

def procesar_libro(pdf_path, memoria, tipo="auto", nombre_libro=None):
    """Process any book and feed patterns into ANIMUS memory with Self-Audit logic."""

    # Soporte para archivos .txt
    if str(pdf_path).lower().endswith('.txt'):
        with open(pdf_path, encoding='utf-8', errors='replace') as f:
            raw_text = f.read()
        chunk_size = 800
        chunks = [raw_text[i:i+chunk_size]
                  for i in range(0, len(raw_text), chunk_size)]
        total_paginas = len(chunks)
        print(f"   Tipo: texto plano | Paginas simuladas: {total_paginas}")
        nuevas_conn = nuevas_words = 0
        tensiones_count = resoluciones_count = 0
        nombre_libro_txt = nombre_libro or Path(str(pdf_path)).stem[:20].lower().replace(" ","_")
        mapa = {**MAPA_SABIDURIA, **MAPA_TECH}

        mapa_extra = {
        "algorithm": "algorithm", "failure": "failure", 
        "bias": "inequality", "blind": "gap", "spot": "gap",
        "corruption": "corruption", "threat": "threat"
        }
        
        mapa.update(mapa_extra)
        
        palabras_tension = set(k for k, v in mapa.items()
                               if v in {"failure","poverty","corruption","fraud","gap",
                                        "crisis","collapse","burnout","inequality",
                                        "bottleneck","vulnerability","limitation","shortage"})
        palabras_resolucion = set(k for k, v in mapa.items()
                                   if v in {"education","cooperation","developed","reform",
                                            "regulation","algorithm","discovered","incentive",
                                            "solution","prevention","innovation","transformed",
                                            "neural","training","framework","automation"})
        
        for i, chunk in enumerate(chunks):
            try:
                # --- NUEVO: AUDITORÍA DE CONTRADICCIONES ---
                alertas = detectar_contradicciones(chunk, mapa, palabras_tension, palabras_resolucion)
                if alertas:
                    for alerta in alertas:
                        print(f"🔍 ANIMUS Crítico: {alerta}")
                        memoria["dudas_sistemicas"] = memoria.get("dudas_sistemicas", {})
                        reforzar(memoria["dudas_sistemicas"], alerta, 1.5)

                palabras = re.findall(r'[a-zA-Záéíóúüñ]{4,}', chunk.lower())
                palabras_set = set(normalizar_token(p) for p in palabras if p not in STOPWORDS)
                
                t_list = [p for p in palabras_set if p in palabras_tension]
                r_list = [p for p in palabras_set if p in palabras_resolucion]
                tensiones_count += len(t_list)
                resoluciones_count += len(r_list)
                
                for t in t_list:
                    token_t = mapa[t]
                    clave_p = f"{nombre_libro_txt}_{token_t}"
                    if clave_p not in memoria["problemas"]:
                        memoria["problemas"][clave_p] = 0.0
                        nuevas_words += 1
                    memoria["problemas"][clave_p] = min(100.0, memoria["problemas"][clave_p] + 1.2)
                    
                for r in r_list:
                    token_r = mapa[r]
                    clave_s = f"{nombre_libro_txt}_{token_r}"
                    if clave_s not in memoria["soluciones"]:
                        memoria["soluciones"][clave_s] = 0.0
                    memoria["soluciones"][clave_s] = min(100.0, memoria["soluciones"][clave_s] + 1.2)

                for t in t_list:
                    for r in r_list:
                        token_t = mapa[t]; token_r = mapa[r]
                        clave_c = f"{nombre_libro_txt}_{token_t}__>{nombre_libro_txt}_{token_r}"
                        if clave_c not in memoria["conexiones"]:
                            memoria["conexiones"][clave_c] = 0.0
                            nuevas_conn += 1
                        memoria["conexiones"][clave_c] = min(100.0, memoria["conexiones"][clave_c] + 1.2)
            except Exception:
                continue
            if (i+1) % 5 == 0 or i+1 == total_paginas:
                print(f"   Chunks: {i+1}/{total_paginas} | Conexiones: {nuevas_conn}")
        return total_paginas, nuevas_conn, nuevas_words, {"tensiones": tensiones_count, "resoluciones": resoluciones_count}

    # --- PROCESAMIENTO PDF ---
    reader = PdfReader(pdf_path)
    total_paginas = len(reader.pages)

    if nombre_libro is None:
        nombre_libro = Path(pdf_path).stem[:20].lower().replace(" ", "_")

    muestra = " ".join(reader.pages[i].extract_text() or "" for i in range(min(10, total_paginas)))
    if tipo == "auto": tipo = detectar_tipo(muestra)

    mapa = MAPA_SABIDURIA if tipo == "wisdom" else {**MAPA_SABIDURIA, **MAPA_TECH}

    palabras_tension = set(k for k, v in mapa.items() if v in {"failure", "poverty", "corruption", "fraud", "gap", "crisis", "collapse", "burnout", "inequality", "bottleneck", "vulnerability", "limitation", "shortage"})
    palabras_resolucion = set(k for k, v in mapa.items() if v in {"education", "cooperation", "developed", "reform", "regulation", "algorithm", "discovered", "incentive", "solution", "prevention", "innovation", "transformed", "neural", "modeled", "optimized", "scaled", "training"})

    print(f"\n📖 Procesando: {nombre_libro} | Tipo: {tipo}")

    paginas_procesadas = 0
    nuevas_conexiones = 0
    nuevas_palabras = 0
    stats = {"tensiones": 0, "resoluciones": 0, "conexiones": 0}

    for i in range(total_paginas):
        try:
            texto = reader.pages[i].extract_text()
        except Exception: continue
        if not texto or len(texto.strip()) < 30: continue

        # --- NUEVO: AUDITORÍA DE CONTRADICCIONES ---
        alertas = detectar_contradicciones(texto, mapa, palabras_tension, palabras_resolucion)
        if alertas:
            for alerta in alertas:
                print(f"🔍 ANIMUS Reflexión: {alerta}")
                memoria["dudas_sistemicas"] = memoria.get("dudas_sistemicas", {})
                # Reforzamos la duda para que pese en el análisis de autoconciencia
                memoria["dudas_sistemicas"][alerta] = memoria["dudas_sistemicas"].get(alerta, 0.0) + 1.5

        palabras_raw = re.findall(r'[a-záéíóúüñ]{4,}', texto.lower())
        palabras_set = set()
        for p in palabras_raw:
            p_norm = normalizar_token(p)
            if p_norm not in STOPWORDS:
                palabras_set.add(p_norm)

        tensiones = [p for p in palabras_set if p in palabras_tension]
        resoluciones = [p for p in palabras_set if p in palabras_resolucion]

        stats["tensiones"] += len(tensiones)
        stats["resoluciones"] += len(resoluciones)

        for p in tensiones:
            token = mapa[p]
            reforzar(memoria["problemas"], f"{nombre_libro}_{token}", 2.0)

        for r in resoluciones:
            token = mapa[r]
            reforzar(memoria["soluciones"], f"{nombre_libro}_{token}", 2.0)

        if tensiones and resoluciones:
            for t in tensiones[:4]:
                for r in resoluciones[:4]:
                    clave = f"{nombre_libro}_{mapa[t]}__>{nombre_libro}_{mapa[r]}"
                    if clave not in memoria["conexiones"]: nuevas_conexiones += 1
                    reforzar(memoria["conexiones"], clave, 1.2)

        # Language learning
        for palabra in palabras_set:
            if palabra in mapa:
                token = mapa[palabra]
                clave_lang = f"{palabra}__={token}"
                if clave_lang not in memoria["lenguaje"]: nuevas_palabras += 1
                reforzar(memoria["lenguaje"], clave_lang, 1.0)

        paginas_procesadas += 1
        if paginas_procesadas % 50 == 0:
            print(f"   Páginas: {paginas_procesadas}/{total_paginas} | Conexiones: {nuevas_conexiones}")

    return paginas_procesadas, nuevas_conexiones, nuevas_palabras, stats


def analisis_autoconciencia(memoria):
    """
    Special analysis: can ANIMUS identify patterns about its OWN limitations
    and suggest improvements based on what it learned?
    """
    lenguaje = memoria["lenguaje"]
    conexiones = memoria["conexiones"]

    # Find tech-related connections
    conn_tech = {k: v for k, v in conexiones.items()
                 if any(t in k for t in ["tech", "meditaciones", "arte_guerra",
                                          "tao", "deep", "algorithm", "neural"])}

    print("\n" + "=" * 65)
    print("  ANÁLISIS DE AUTOCONCIENCIA — ¿Qué sabe ANIMUS de sí mismo?")
    print("=" * 65)

    # Self-relevant connections
    self_tokens = {"bottleneck", "limitation", "shortage", "gap",
                   "algorithm", "neural", "training", "optimized",
                   "scaled", "transformed", "education"}

    self_connections = []
    for k, v in sorted(conexiones.items(), key=lambda x: -x[1]):
        partes = k.split("__>")
        if len(partes) != 2:
            continue
        token_p = partes[0].split("_")[-1]
        token_s = partes[1].split("_")[-1]
        if token_p in self_tokens or token_s in self_tokens:
            word_p = traducir(token_p, lenguaje)
            word_s = traducir(token_s, lenguaje)
            self_connections.append((word_p, word_s, v, k))

    if self_connections:
        print("\n  Patrones relevantes para ANIMUS:")
        for word_p, word_s, v, k in self_connections[:12]:
            fuente = k.split("_")[0] if "_" in k else "?"
            print(f"    [{fuente}] {word_p} → {word_s}: {v:.1f}")

    # Self-improvement suggestions from connections
    print("\n  Ideas de mejora que ANIMUS puede articular:")

    sugerencias = []
    for word_p, word_s, v, k in self_connections[:8]:
        if word_p != word_s and v > 1.0:
            sugerencias.append(f"    • Si el problema es '{word_p}', "
                                f"la solución detectada es '{word_s}'")

    if sugerencias:
        for s in sugerencias[:6]:
            print(s)
    else:
        print("    Aún no hay suficientes conexiones técnicas")

    # Vocabulary of self-awareness
    palabras_autoconciencia = [k.split("__=")[0] for k in lenguaje
                                if k.split("__=")[1] in self_tokens]
    if palabras_autoconciencia:
        print(f"\n  Vocabulario técnico/autoconsciente aprendido:")
        print(f"    {', '.join(sorted(set(palabras_autoconciencia))[:15])}")

    print("=" * 65)


def comparar_fuentes(memoria, nombre_libro):
    """Compare new book connections with existing memory."""
    lenguaje = memoria["lenguaje"]
    conexiones = memoria["conexiones"]

    conn_libro = {k: v for k, v in conexiones.items() if k.startswith(nombre_libro)}
    conn_previas = {k: v for k, v in conexiones.items() if not k.startswith(nombre_libro)}

    print(f"\n  Conexiones del libro: {len(conn_libro)}")
    print(f"  Conexiones previas:   {len(conn_previas)}")

    # Top new connections
    print(f"\n  Top patrones emergentes de {nombre_libro}:")
    for k, v in sorted(conn_libro.items(), key=lambda x: -x[1])[:8]:
        partes = k.split("__>")
        if len(partes) == 2:
            token_p = partes[0].split("_")[-1]
            token_s = partes[1].split("_")[-1]
            word_p = traducir(token_p, lenguaje)
            word_s = traducir(token_s, lenguaje)
            print(f"    {word_p} → {word_s}: {v:.1f}")

    # Convergences with previous knowledge
    convergencias = []
    for k_n, v_n in conn_libro.items():
        partes_n = k_n.split("__>")
        if len(partes_n) != 2:
            continue
        tp_n = partes_n[0].split("_")[-1]
        ts_n = partes_n[1].split("_")[-1]
        for k_p, v_p in conn_previas.items():
            partes_p = k_p.split("__>")
            if len(partes_p) != 2:
                continue
            tp_p = partes_p[0].split("_")[-1]
            ts_p = partes_p[1].split("_")[-1]
            if tp_n == tp_p and ts_n == ts_p:
                word_p = traducir(tp_n, lenguaje)
                word_s = traducir(ts_n, lenguaje)
                convergencias.append({
                    "pattern": f"{word_p} → {word_s}",
                    "nuevo": v_n, "previo": v_p,
                    "total": v_n + v_p
                })

    convergencias.sort(key=lambda x: -x["total"])
    if convergencias:
        print(f"\n  Convergencias con conocimiento previo:")
        for c in convergencias[:6]:
            print(f"    ✦ {c['pattern']:35} Nuevo:{c['nuevo']:.1f}  Previo:{c['previo']:.1f}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Universal Book Processor")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("memoria", nargs="?", default="memoria_business.json",
                        help="Path to memoria JSON (default: memoria_business.json)")
    parser.add_argument("--tipo", choices=["wisdom", "tech", "auto"], default="auto",
                        help="Book type (default: auto-detect)")
    parser.add_argument("--nombre", help="Custom book name for tracking")
    args = parser.parse_args()

    if not Path(args.pdf).exists():
        print(f"Error: {args.pdf} no encontrado.")
        sys.exit(1)
    if not Path(args.memoria).exists():
        print(f"Error: {args.memoria} no encontrado.")
        sys.exit(1)

    with open(args.memoria, encoding="utf-8") as f:
        memoria = json.load(f)

    memoria["problemas"] = dict(memoria.get("problemas", {}))
    memoria["soluciones"] = dict(memoria.get("soluciones", {}))
    memoria["conexiones"] = dict(memoria.get("conexiones", {}))
    memoria["lenguaje"] = dict(memoria.get("lenguaje", {}))

    nombre = args.nombre or Path(args.pdf).stem[:20].lower().replace(" ", "_")

    paginas, nuevas_conn, nuevas_words, stats = procesar_libro(
        args.pdf, memoria, tipo=args.tipo, nombre_libro=nombre
    )

    print(f"\n✅ Procesamiento completado:")
    print(f"   Páginas leídas:    {paginas}")
    print(f"   Conexiones nuevas: {nuevas_conn}")
    print(f"   Palabras nuevas:   {nuevas_words}")
    print(f"   Tensiones:         {stats['tensiones']}")
    print(f"   Resoluciones:      {stats['resoluciones']}")

    comparar_fuentes(memoria, nombre)
    analisis_autoconciencia(memoria)

    memoria["ultima_actualizacion"] = datetime.now().isoformat()
    with open(args.memoria, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Memoria actualizada: {args.memoria}")
    print(f"   Total conexiones: {len(memoria['conexiones'])}")
    print(f"   Vocabulario total: {len(memoria['lenguaje'])} palabras")