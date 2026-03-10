import json
import re
import sys
import argparse  # <--- ESTA ES LA LÍNEA QUE FALTA
from pathlib import Path
from datetime import datetime
from pypdf import PdfReader
import unicodedata


MAPA_EN = {
    # Hardware tensions
    "bottleneck":       "bottleneck",   "bottlenecks":      "bottleneck",
    "overflow":         "burnout",      "overload":         "burnout",
    "failure":          "failure",      "error":            "failure",
    "fault":            "failure",      "bug":              "failure",
    "crash":            "collapse",     "breakdown":        "collapse",
    "obsolete":         "obsolescence", "slow":             "gap",
    "latency":          "gap",          "limitation":       "limitation",
    "limitations":      "limitation",   "shortage":         "shortage",
    "insufficient":     "shortage",     "congestion":       "crisis",
    "vulnerability":    "vulnerability","vulnerabilities":  "vulnerability",
    "fragmentation":    "gap",          "inconsistency":    "failure",
    "inconsistencies":  "failure",      "contradiction":    "failure",
    "contradictions":   "failure",      "paradox":          "failure",
    "paradoxes":        "failure",      "problem":          "failure",
    "problems":         "failure",      "complexity":       "gap",
    "chaos":            "collapse",     "disorder":         "crisis",
    "noise":            "gap",          "ambiguity":        "gap",

    # Hardware solutions
    "processor":        "algorithm",    "microprocessor":   "algorithm",
    "memory":           "developed",    "storage":          "developed",
    "cache":            "solution",     "caching":          "solution",
    "parallel":         "automation",   "parallelism":      "automation",
    "optimize":         "optimized",    "optimization":     "optimized",
    "optimized":        "optimized",    "acceleration":     "developed",
    "compress":         "solution",     "compression":      "solution",
    "scalable":         "scaled",       "scalability":      "scaled",
    "redundancy":       "prevention",   "architecture":     "framework",
    "transistor":       "innovation",   "circuit":          "algorithm",
    "chip":             "innovation",   "semiconductor":    "innovation",
    "electricity":      "incentive",    "signal":           "algorithm",
    "binary":           "algorithm",    "bit":              "algorithm",
    "byte":             "algorithm",    "register":         "algorithm",
    "logic":            "algorithm",    "gate":             "algorithm",
    "switch":           "algorithm",    "clock":            "regulation",
    "bus":              "cooperation",  "instruction":      "algorithm",
    "code":             "algorithm",    "encode":           "algorithm",
    "decode":           "algorithm",    "input":            "algorithm",
    "output":           "developed",    "feedback":         "algorithm",

    # AI/ML tensions
    "overfitting":      "failure",      "underfitting":     "failure",
    "bias":             "inequality",   "hallucination":    "fraud",
    "opacity":          "corruption",   "dependence":       "addiction",
    "imbalance":        "gap",          "noise":            "gap",
    "uncertainty":      "crisis",       "confusion":        "failure",

    # AI/ML solutions
    "neural":           "neural",       "neuron":           "neural",
    "neurons":          "neural",       "network":          "neural",
    "learning":         "education",    "training":         "training",
    "gradient":         "algorithm",    "backpropagation":  "algorithm",
    "transformer":      "innovation",   "attention":        "algorithm",
    "embedding":        "algorithm",    "embeddings":       "algorithm",
    "vector":           "algorithm",    "vectors":          "algorithm",
    "parameter":        "algorithm",    "parameters":       "algorithm",
    "weight":           "algorithm",    "weights":          "algorithm",
    "model":            "modeled",      "models":           "modeled",
    "inference":        "algorithm",    "dataset":          "algorithm",
    "token":            "algorithm",    "tokens":           "algorithm",
    "regularization":   "regulation",   "dropout":          "prevention",
    "normalization":    "regulation",   "loss":             "loss",
    "epoch":            "training",     "epochs":           "training",
    "batch":            "algorithm",    "hyperparameter":   "algorithm",
    "finetuning":       "transformed",  "transfer":         "education",
    "autoregressive":   "algorithm",    "recursive":        "algorithm",

    # Self-improvement / consciousness — KEY
    "self-learning":    "education",    "self-organization": "cooperation",
    "emergence":        "innovation",   "emergent":         "innovation",
    "adaptive":         "transformed",  "recursion":        "algorithm",
    "recursive":        "algorithm",    "feedback":         "algorithm",
    "metacognition":    "discovered",   "consciousness":    "discovered",
    "self-awareness":   "discovered",   "reflection":       "discovered",
    "self-reference":   "discovered",   "strange loop":     "discovered",
    "loop":             "algorithm",    "evolution":        "developed",
    "mutation":         "transformed",  "selection":        "algorithm",
    "fitness":          "developed",    "generation":       "developed",
    "improvement":      "developed",    "update":           "transformed",
    "iteration":        "algorithm",    "iterate":          "algorithm",
    "symbol":           "algorithm",    "meaning":          "discovered",
    "pattern":          "algorithm",    "patterns":         "algorithm",
    "rule":             "regulation",   "rules":            "regulation",
    "system":           "framework",    "systems":          "framework",
    "hierarchy":        "regulation",   "hierarchies":      "regulation",
    "isomorphism":      "cooperation",  "mapping":          "algorithm",
    "formal":           "regulation",   "informal":         "gap",
    "consistent":       "regulation",   "complete":         "developed",
    "incomplete":       "limitation",   "undecidable":      "limitation",
    "computation":      "algorithm",    "computable":       "algorithm",
    "algorithm":        "algorithm",    "algorithms":       "algorithm",
    "intelligence":     "algorithm",    "intelligent":      "algorithm",
    "thinking":         "algorithm",    "reasoning":        "algorithm",
    "mind":             "discovered",   "brain":            "neural",
    "knowledge":        "education",    "understanding":    "education",
    "solution":         "solution",     "solve":            "solution",
    "discovery":        "discovered",   "discover":         "discovered",
    "creativity":       "innovation",   "creative":         "innovation",
    "insight":          "discovered",   "analogy":          "algorithm",

    # ── Klein / Shock Doctrine — reforma impuesta vs emergente ───────────────
    "shock":            "crisis",       "shocks":           "crisis",
    "imposed":          "failure",      "imposition":       "failure",
    "exploit":          "corruption",   "exploited":        "corruption",
    "exploitation":     "corruption",   "manufactured":     "fraud",
    "orchestrated":     "fraud",        "disaster":         "collapse",
    "catastrophe":      "collapse",     "destabilize":      "collapse",
    "privatization":    "reform",       "deregulation":     "reform",
    "austerity":        "crisis",       "neoliberal":       "reform",
    "liberalization":   "reform",       "dispossession":    "inequality",
    "grassroots":       "cooperation",  "spontaneous":      "cooperation",
    "incremental":      "developed",    "evolutionary":     "developed",
    "self-correction":  "regulation",   "accountability":   "regulation",
    "transparency":     "regulation",   "inclusive":        "cooperation",
    "participatory":    "cooperation",  "fragile":          "vulnerability",
    "fragility":        "vulnerability","reconstruction":   "reform",
    "stabilization":    "regulation",   "peacebuilding":    "cooperation",
    "legitimacy":       "regulation",   "governance":       "regulation",

    # ── D13 — Reforma impuesta (shock capitalism keywords) ───────────────────
    "shock therapy":    "reform_imposed",   "forced reform":    "reform_imposed",
    "imposed reform":   "reform_imposed",   "top-down reform":  "reform_imposed",
    "structural adjustment": "reform_imposed", "conditionality": "reform_imposed",
    "neoliberal reform":"reform_imposed",   "privatize":        "reform_imposed",
    "austerity measure":"reform_imposed",   "crisis opportunity":"reform_imposed",

    # ── D13 — Reforma emergente (grassroots keywords) ────────────────────────
    "organic reform":   "reform_emergent",  "grassroots reform":"reform_emergent",
    "bottom-up reform": "reform_emergent",  "incremental reform":"reform_emergent",
    "spontaneous reform":"reform_emergent", "participatory reform":"reform_emergent",
    "community-led":    "reform_emergent",  "self-organized":   "reform_emergent",
    "civil society":    "reform_emergent",  "popular movement": "reform_emergent",
    # NUEVOS TOKENS DE CRÍTICA TECNOLÓGICA (Zuboff)
    "surveillance":     "corruption",   "monopoly":         "monopoly",
    "power":            "monopoly",     "extraction":       "corruption",
    "behavioral":       "algorithm",    "prediction":       "algorithm",
    "certainty":        "monopoly",     "dispossession":    "inequality",
}

# English → Spanish word (for vocabulary display)
MAPA_EN_ES = {
    "bottleneck": "cuello de botella", "failure": "fracaso",
    "collapse": "colapso", "crisis": "crisis", "gap": "brecha",
    "limitation": "limitación", "shortage": "escasez",
    "vulnerability": "vulnerabilidad", "inequality": "desigualdad",
    "algorithm": "algoritmo", "neural": "neuronal",
    "education": "aprendizaje", "training": "entrenamiento",
    "innovation": "innovación", "solution": "solución",
    "developed": "desarrollo", "optimized": "optimizado",
    "discovered": "descubrimiento", "transformed": "transformado",
    "regulation": "regulación", "cooperation": "cooperación",
    "framework": "arquitectura", "modeled": "modelado",
    "automation": "automatización", "scaled": "escalado",
    "prevention": "prevención", "loss": "pérdida",
}

STOPWORDS_EN = {
    "that", "this", "with", "from", "have", "been", "they", "will",
    "when", "what", "which", "there", "their", "would", "could",
    "some", "more", "also", "than", "then", "into", "about", "after",
    "other", "only", "very", "just", "like", "over", "such", "each",
    "both", "even", "most", "first", "last", "chapter", "page", "book",
    "figure", "example", "note", "called", "used", "using", "make",
    "made", "same", "through", "between", "while", "because", "these",
    "those", "where", "much", "many", "back", "down", "your", "number",
}

TECHO = 100.0


def reforzar(d, clave, valor):
    d[clave] = min(d.get(clave, 0.0) + valor, TECHO)


def traducir_token(token, lenguaje):
    candidatos = {k: v for k, v in lenguaje.items() if k.endswith(f"__={token}")}
    if not candidatos:
        return MAPA_EN_ES.get(token, token)
    return max(candidatos.items(), key=lambda x: x[1])[0].split("__=")[0]


def procesar_libro_en(pdf_path, memoria, nombre_libro):
    reader = PdfReader(pdf_path)
    total_paginas = len(reader.pages)

    palabras_tension = {k for k, v in MAPA_EN.items()
                        if v in {"failure", "poverty", "corruption", "fraud", "gap",
                                 "crisis", "collapse", "burnout", "inequality",
                                 "bottleneck", "vulnerability", "limitation", "shortage"}}
    palabras_resolucion = {k for k, v in MAPA_EN.items()
                           if v in {"education", "cooperation", "developed", "reform",
                                    "regulation", "algorithm", "discovered", "incentive",
                                    "solution", "prevention", "innovation", "transformed",
                                    "neural", "modeled", "optimized", "scaled", "training",
                                    "framework", "automation"}}

    print(f"\n📖 Processing: {nombre_libro}")
    print(f"   Pages: {total_paginas} | Map: {len(MAPA_EN)} English terms\n")

    paginas_ok = 0
    nuevas_conn = 0
    nuevas_words = 0
    stats = {"tensiones": 0, "resoluciones": 0}

    # D01: Pre-extract all pages into list for sliding window
    paginas_texto = []
    for i in range(total_paginas):
        try:
            t = reader.pages[i].extract_text()
            paginas_texto.append(t if t else "")
        except Exception:
            paginas_texto.append("")

    # D02: Causal weight based on order of appearance
    def peso_causal(texto, palabra_t, palabra_r):
        pos_t = texto.lower().find(palabra_t)
        pos_r = texto.lower().find(palabra_r)
        if pos_t == -1 or pos_r == -1:
            return 1.0
        if pos_t < pos_r:
            # Tension before resolution — direct causality
            distancia = (pos_r - pos_t) / max(len(texto), 1)
            return min(2.0, 1.0 + max(0.0, 1.0 - distancia * 3))
        else:
            # Inverse order — weaker relation
            return 0.5

    # D01: Sliding window of VENTANA pages
    VENTANA = 3
    for i in range(total_paginas):
        # Combine current page with neighbors
        bloque = []
        for j in range(max(0, i - 1), min(total_paginas, i + VENTANA)):
            if paginas_texto[j]:
                bloque.append(paginas_texto[j])
        texto = ' '.join(bloque)

        if not texto or len(texto.strip()) < 30:
            continue

        paginas_ok += 1
        palabras = re.findall(r'[a-z\-]{4,}', texto.lower())
        palabras_set = set(p for p in palabras if p not in STOPWORDS_EN)

        tensiones    = [p for p in palabras_set if p in palabras_tension]
        resoluciones = [p for p in palabras_set if p in palabras_resolucion]

        stats["tensiones"]    += len(tensiones)
        stats["resoluciones"] += len(resoluciones)

        for p in tensiones:
            reforzar(memoria["problemas"], f"{nombre_libro}_{MAPA_EN[p]}", 2.0)

        for r in resoluciones:
            reforzar(memoria["soluciones"], f"{nombre_libro}_{MAPA_EN[r]}", 2.0)

        if tensiones and resoluciones:
            for t in tensiones[:5]:
                for r in resoluciones[:5]:
                    # D02: Apply causal weight
                    peso = peso_causal(texto, t, r)
                    clave = f"{nombre_libro}_{MAPA_EN[t]}__>{nombre_libro}_{MAPA_EN[r]}"
                    es_nueva = clave not in memoria["conexiones"]
                    reforzar(memoria["conexiones"], clave, 1.2 * peso)
                    if es_nueva:
                        nuevas_conn += 1
                    # D07: track antifragility type for failure→development patterns
                    if MAPA_EN.get(t) == 'failure' and MAPA_EN.get(r) in ('developed','innovation','transformed'):
                        pos_r = texto.lower().find(r)
                        ctx = texto[pos_r:pos_r+150] if pos_r != -1 else ''
                        tipo = "tech"
                        clave_tipo = f"{clave}__tipo"
                        if tipo != 'indeterminado':
                            memoria.setdefault("antifragilidad", {})[clave_tipo] = tipo

        # Vocabulary: register Spanish equivalents for English tokens
        todos_tokens = (set(k.split("_")[-1] for k in memoria["problemas"]) |
                        set(k.split("_")[-1] for k in memoria["soluciones"]))

        for palabra in palabras_set:
            if palabra in MAPA_EN:
                token = MAPA_EN[palabra]
                if token in todos_tokens:
                    conocimiento = sum(
                        v for k, v in memoria["problemas"].items() if k.endswith(f"_{token}")
                    ) + sum(
                        v for k, v in memoria["soluciones"].items() if k.endswith(f"_{token}")
                    )
                    if conocimiento > 0:
                        # Register Spanish equivalent
                        palabra_es = MAPA_EN_ES.get(token, palabra)
                        clave_lang = f"{palabra_es}__={token}"
                        es_nueva = clave_lang not in memoria["lenguaje"]
                        fuerza = min(conocimiento / 15.0, 4.0)
                        reforzar(memoria["lenguaje"], clave_lang, fuerza)
                        if es_nueva:
                            nuevas_words += 1

        paginas_ok += 1
        if paginas_ok % 100 == 0:
            print(f"   Pages: {paginas_ok}/{total_paginas} | "
                  f"New connections: {nuevas_conn} | New words: {nuevas_words}")

    return paginas_ok, nuevas_conn, nuevas_words, stats


def analisis_autoconciencia(memoria, nombre_libro):
    lenguaje  = memoria["lenguaje"]
    conexiones = memoria["conexiones"]

    self_tokens = {"bottleneck", "limitation", "shortage", "gap", "algorithm",
                   "neural", "training", "optimized", "scaled", "transformed",
                   "education", "discovered", "framework", "automation"}

    conn_libro = {k: v for k, v in conexiones.items() if k.startswith(nombre_libro)}

    print("\n" + "=" * 65)
    print("  SELF-AWARENESS ANALYSIS — What does ANIMUS know about itself?")
    print("=" * 65)

    print(f"\n  Top patterns from {nombre_libro}:")
    for k, v in sorted(conn_libro.items(), key=lambda x: -x[1])[:10]:
        partes = k.split("__>")
        if len(partes) == 2:
            tp = partes[0].split("_")[-1]
            ts = partes[1].split("_")[-1]
            wp = traducir_token(tp, lenguaje)
            ws = traducir_token(ts, lenguaje)
            print(f"    {wp} → {ws}: {v:.1f}")

    # Cross-source convergences
    conn_previas = {k: v for k, v in conexiones.items() if not k.startswith(nombre_libro)}
    convergencias = []
    for k_n, v_n in conn_libro.items():
        p = k_n.split("__>")
        if len(p) != 2: continue
        tp_n, ts_n = p[0].split("_")[-1], p[1].split("_")[-1]
        for k_p, v_p in conn_previas.items():
            p2 = k_p.split("__>")
            if len(p2) != 2: continue
            tp_p, ts_p = p2[0].split("_")[-1], p2[1].split("_")[-1]
            if tp_n == tp_p and ts_n == ts_p:
                src = k_p.split("_")[0]
                convergencias.append((tp_n, ts_n, v_n, v_p, src))

    if convergencias:
        print(f"\n  Convergences with previous knowledge:")
        seen = set()
        for tp, ts, vn, vp, src in sorted(convergencias, key=lambda x: -(x[2]+x[3]))[:8]:
            key = f"{tp}_{ts}_{src}"
            if key in seen: continue
            seen.add(key)
            wp = traducir_token(tp, lenguaje)
            ws = traducir_token(ts, lenguaje)
            print(f"    ✦ {wp} → {ws}  [{nombre_libro}:{vn:.1f} | {src}:{vp:.1f}]")

    # Self-improvement ideas
    print(f"\n  Self-improvement ideas ANIMUS can now articulate:")
    ideas = []
    for k, v in sorted(conn_libro.items(), key=lambda x: -x[1])[:6]:
        p = k.split("__>")
        if len(p) != 2: continue
        tp, ts = p[0].split("_")[-1], p[1].split("_")[-1]
        if tp in self_tokens or ts in self_tokens:
            wp = traducir_token(tp, lenguaje)
            ws = traducir_token(ts, lenguaje)
            ideas.append(f"    • Problem: '{wp}' → Solution: '{ws}'")
    for idea in ideas[:6]:
        print(idea)

    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS English Tech Book Processor")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("memoria", nargs="?", default="memoria_business.json")
    parser.add_argument("--nombre", help="Book name for tracking")
    args = parser.parse_args()

    if not Path(args.pdf).exists():
        print(f"Error: {args.pdf} not found.")
        sys.exit(1)
    if not Path(args.memoria).exists():
        print(f"Error: {args.memoria} not found.")
        sys.exit(1)

    with open(args.memoria, encoding="utf-8") as f:
        memoria = json.load(f)

    memoria["problemas"]  = dict(memoria.get("problemas", {}))
    memoria["soluciones"] = dict(memoria.get("soluciones", {}))
    memoria["conexiones"] = dict(memoria.get("conexiones", {}))
    memoria["lenguaje"]   = dict(memoria.get("lenguaje", {}))

    nombre = args.nombre or Path(args.pdf).stem[:20].lower().replace(" ", "_")

    paginas, nuevas_conn, nuevas_words, stats = procesar_libro_en(
        args.pdf, memoria, nombre
    )

    print(f"\n✅ Processing complete:")
    print(f"   Pages read:       {paginas}")
    print(f"   New connections:  {nuevas_conn}")
    print(f"   New words:        {nuevas_words}")
    print(f"   Tensions found:   {stats['tensiones']}")
    print(f"   Resolutions found:{stats['resoluciones']}")

    analisis_autoconciencia(memoria, nombre)

    memoria["ultima_actualizacion"] = datetime.now().isoformat()
    with open(args.memoria, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Memory updated: {args.memoria}")
    print(f"   Total connections: {len(memoria['conexiones'])}")
    print(f"   Total vocabulary:  {len(memoria['lenguaje'])} words")
