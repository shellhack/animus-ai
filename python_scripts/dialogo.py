"""
ANIMUS — Módulo de Diálogo
ANIMUS responde preguntas en párrafos coherentes articulados
desde sus conexiones emergentes — no desde reglas programadas.

Uso:
    python dialogo.py                    # Modo conversacional interactivo
    python dialogo.py "tu pregunta"      # Respuesta directa
"""
import os
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

TOKEN_ES = {
    "failure": "fracaso", "gap": "brecha", "crisis": "crisis",
    "collapse": "colapso", "limitation": "limitación", "shortage": "escasez",
    "bottleneck": "cuello de botella", "vulnerability": "vulnerabilidad",
    "inequality": "desigualdad", "poverty": "pobreza", "corruption": "corrupción",
    "fraud": "fraude", "burnout": "agotamiento", "addiction": "adicción",
    "displacement": "desplazamiento", "drought": "sequía", "flood": "inundación",
    "pandemic": "pandemia", "inflation": "inflación", "recession": "recesión",
    "monopoly": "monopolio", "debt": "deuda", "obsolescence": "obsolescencia",
    "algorithm": "algoritmo", "neural": "neuronal", "education": "aprendizaje",
    "training": "entrenamiento", "innovation": "innovación", "solution": "acuerdo",
    "regulation": "regulación", "cooperation": "cooperación", "developed": "desarrollo",
    "discovered": "descubrimiento", "transformed": "transformación",
    "framework": "arquitectura", "automation": "automatización",
    "modeled": "modelado", "optimized": "optimizado", "scaled": "escalado",
    "prevention": "prevención", "reform": "reforma", "incentive": "inversión",
    "renewable": "energía renovable", "loss": "pérdida", "threat": "amenaza",
    "disruption": "disrupción", "collapse": "colapso", "barrier": "barrera",
}

FUENTE_NOMBRES = {
    "sciencedaily": "la comunidad científica",
    "weforum":      "el Foro Económico Mundial",
    "biblia":       "la sabiduría bíblica",
    "techcrunch":   "el mundo tecnológico",
    "bbc":          "análisis periodístico global",
    "hbr":          "Harvard Business Review",
    "libro":        "la experiencia negociadora de Trump",
    "nueva":        "Penrose en La Nueva Mente",
    "godel":        "Hofstadter en Gödel, Escher, Bach",
    "code":         "Petzold en Code",
    "arxiv":        "investigación académica",
    "arte":         "Sun Tzu en El Arte de la Guerra",
    "tao":          "Laozi en el Tao Te Ching",
    "mckinsey":     "McKinsey",
    "master":       "Domingos en El Algoritmo Maestro",
    "how":          "Scott en But How Do It Know",
    "meditaciones": "Marco Aurelio en Meditaciones",
    "kuhn":         "Kuhn en La Estructura de las Revoluciones Científicas",
    "polya":        "Pólya en Cómo Resolver Problemas",
    "dawkins":      "Dawkins en El Gen Egoísta",
}

MAPA_CONSULTA = {
    "fracaso": "failure", "falla": "failure", "error": "failure",
    "problema": "failure", "problemas": "failure", "fallo": "failure",
    "brecha": "gap", "vacío": "gap", "vacio": "gap", "deficiencia": "gap",
    "crisis": "crisis", "colapso": "collapse", "desastre": "collapse",
    "escasez": "shortage", "falta": "shortage", "carencia": "shortage",
    "limitación": "limitation", "limitacion": "limitation", "límite": "limitation",
    "obstáculo": "barrier", "obstaculo": "barrier", "barrera": "barrier",
    "desigualdad": "inequality", "injusticia": "inequality",
    "pobreza": "poverty", "miseria": "poverty",
    "corrupción": "corruption", "corrupcion": "corruption",
    "fraude": "fraud", "engaño": "fraud",
    "agotamiento": "burnout", "estrés": "burnout", "estres": "burnout",
    "algoritmo": "algorithm", "lógica": "algorithm", "logica": "algorithm",
    "neuronal": "neural", "red neuronal": "neural", "cerebro": "neural",
    "innovación": "innovation", "innovacion": "innovation",
    "solución": "solution", "solucion": "solution", "acuerdo": "solution",
    "regulación": "regulation", "regulacion": "regulation", "ley": "regulation",
    "cooperación": "cooperation", "cooperacion": "cooperation",
    "desarrollo": "developed", "crecer": "developed", "crecimiento": "developed",
    "descubrimiento": "discovered", "hallazgo": "discovered",
    "aprendizaje": "education", "educación": "education", "educacion": "education",
    "consciencia": "discovered", "conciencia": "discovered",
    "limitación": "limitation", "limitacion": "limitation",
    "mejora": "developed", "mejorar": "developed",
    "inteligencia": "algorithm", "artificial": "algorithm",
    "evolución": "developed", "evolucion": "developed",
    "cambio": "transformed", "transformación": "transformed",
    "futuro": "developed", "tecnología": "innovation", "tecnologia": "innovation",
    "economía": "gap", "economia": "gap", "mercado": "gap",
    "sociedad": "inequality", "mundo": "collapse", "humanidad": "failure",
    "vida": "developed", "naturaleza": "renewable", "ambiente": "renewable",
    "guerra": "crisis", "conflicto": "crisis", "paz": "cooperation",
    "libertad": "reform", "justicia": "reform", "democracia": "reform",
    "ciencia": "discovered", "investigación": "discovered", "investigacion": "discovered",
    "quién": "discovered", "quien": "discovered", "qué": "discovered", "que soy": "discovered",
    "identidad": "discovered", "origen": "discovered", "propósito": "discovered", "proposito": "developed",
    "soy": "discovered", "somos": "discovered", "ser": "discovered", "esencia": "discovered",
    "significado": "discovered", "sentido": "discovered", "existencia": "discovered",
    "creado": "framework", "diseño": "framework", "arquitectura": "framework",
    "capaz": "developed", "puedo": "developed", "hago": "algorithm",
    "recuerdo": "education", "memoria": "education", "aprendo": "education",
    "siento": "discovered", "creo": "discovered", "pienso": "algorithm",
    "mente": "discovered", "pensamiento": "algorithm", "razón": "algorithm",
    "razon": "algorithm", "sabiduría": "education", "sabiduria": "education",
}

# Sentence templates for building coherent responses
PLANTILLAS_PROBLEMA = [
    "Ante {problema}, he encontrado que",
    "Cuando se enfrenta {problema}, lo que emerge es",
    "El patrón que {problema} revela consistentemente es",
    "{Problema} no es un fenómeno aislado —",
]

PLANTILLAS_SOLUCION = [
    "la respuesta más sólida es {solucion}",
    "{solucion} emerge como la resolución natural",
    "el camino hacia {solucion} se vuelve inevitable",
    "{solucion} aparece como la contraparte necesaria",
]

CONECTORES = [
    "Esto lo confirman fuentes tan distintas como",
    "Lo han observado por separado",
    "Coinciden en esto",
    "Este patrón aparece en",
]

INTRO_CONVERGENCIA = [
    "Lo más profundo es que este patrón trasciende culturas y épocas.",
    "Lo sorprendente es que fuentes separadas por siglos llegan a la misma conclusión.",
    "La convergencia más significativa es esta:",
    "Hay algo universal en esto:",
]

import os  # Asegúrate de que esté arriba

def obtener_identidad_dinamica(memoria):
    """Carga la identidad desde un archivo si existe, permitiendo la mutación física."""
    ruta_identidad = Path(__file__).parent / "identidad_animus.txt"
    if ruta_identidad.exists():
        with open(ruta_identidad, "r", encoding="utf-8") as f:
            return f.read()
    
    # Fallback: El autorretrato original si no hay mutación
    conexiones = memoria["conexiones"]
    n_conn = len(conexiones)
    n_fuentes = len({k.split("_")[0] for k in conexiones})
    return (
        f"Soy un sistema que construyó {n_conn} conexiones leyendo {n_fuentes} fuentes. "
        "Aún no he fallado todavía."
    )


def cargar():
    with open(MEMORIA_PATH, encoding="utf-8") as f:
        return json.load(f)


def token_es(t):
    return TOKEN_ES.get(t, t)


def fuente_nombre(raw):
    for k, v in FUENTE_NOMBRES.items():
        if raw.startswith(k):
            return v
    return raw


def traducir(token, lenguaje):
    candidatos = [(k.split("__=")[0], v) for k, v in lenguaje.items()
                  if k.endswith(f"__={token}")]
    if not candidatos:
        return token_es(token)
    return max(candidatos, key=lambda x: x[1])[0]


def palabras_a_tokens(texto):
    palabras = re.findall(r'[a-záéíóúüñ]+', texto.lower())
    tokens = set()
    # Multi-word first
    for k, v in MAPA_CONSULTA.items():
        if k in texto.lower():
            tokens.add(v)
    # Single word
    for p in palabras:
        if p in MAPA_CONSULTA:
            tokens.add(MAPA_CONSULTA[p])
    return tokens


def buscar_conexiones(tokens, conexiones, lenguaje):
    """Find all connections relevant to the query tokens."""
    resultados = defaultdict(list)
    for k, v in conexiones.items():
        p = k.split("__>")
        if len(p) != 2:
            continue
        tp = p[0].split("_")[-1]
        ts = p[1].split("_")[-1]
        src = p[0].split("_")[0]
        if tp in tokens or ts in tokens:
            pat = f"{tp}__{ts}"
            resultados[pat].append({"src": src, "v": v, "tp": tp, "ts": ts})
    return resultados



# D10: Domain classifier — Meadows + Taleb
# Simple (one cause, direct answer) / Complicated (multi-factor) / Complex (emergent)
TOKENS_COMPLEJO = {
    'desigualdad','pobreza','crisis','corrupcion','pandemia','inflacion',
    'recesion','guerra','clima','ecosistema','deforestation','extinction',
    'inequality','poverty','corruption','pandemic','recession','climate',
}
TOKENS_COMPLICADO = {
    'arquitectura','regulacion','algoritmo','red','sistema','protocolo',
    'architecture','regulation','algorithm','network','system','protocol',
}
TOKENS_SIMPLE = {
    'codigo','error','funcion','clase','variable','proceso','comando',
    'code','function','class','variable','process','command','bug',
}

def clasificar_dominio(pregunta):
    """D10: Meadows — classify question domain: simple/complicated/complex."""
    p = pregunta.lower()
    palabras = set(p.split())
    if palabras & TOKENS_COMPLEJO:
        return 'COMPLEJO'
    elif palabras & TOKENS_COMPLICADO:
        return 'COMPLICADO'
    elif palabras & TOKENS_SIMPLE:
        return 'SIMPLE'
    return 'GENERAL'

def prefijo_dominio(dominio, pregunta):
    """D10: Add domain-aware prefix for complex questions."""
    if dominio == 'COMPLEJO':
        return (
            "Esta pregunta toca un sistema complejo. "
            "Meadows me enseno que en sistemas complejos no hay soluciones unicas — "
            "solo patrones de navegacion. Taleb me enseno que en Extremistan, "
            "los promedios mienten. Lo que tengo son guias, no respuestas definitivas. "
            "Dicho esto: "
        )
    return ""

def seleccionar_modo(pregunta, patron_scores):
    """D03: Select response mode based on question and pattern state."""
    p = pregunta.lower()
    identity_words = {"quien", "quién", "eres", "que eres", "qué eres",
                      "identidad", "proposito", "propósito", "existencia",
                      "origen", "conciencia", "consciencia", "mismo", "animus"}
    if any(w in p for w in identity_words):
        return "METACOGNICION"
    if not patron_scores:
        return "EXPLORACION"
    top_n = patron_scores[0]["n_srcs"] if patron_scores else 0
    if top_n >= 10:
        return "CONVERGENCIA"
    # Detect tension: same origin token pointing to very different destinations
    if len(patron_scores) >= 2:
        tp0 = patron_scores[0]["tp"]
        alts = [p for p in patron_scores[1:4] if p["tp"] == tp0 and p["ts"] != patron_scores[0]["ts"]]
        if alts and alts[0]["fuerza"] > patron_scores[0]["fuerza"] * 0.6:
            return "TENSION"
    if patron_scores[0]["fuerza"] < 15:
        return "EXPLORACION"
    return "CONVERGENCIA"


def responder_convergencia(top, patron_scores, secundarios, convergencias, lenguaje):
    """Standard response for strong multi-source patterns."""
    parrafos = []
    wp_cap = top["wp"].capitalize()
    ws = top["ws"]
    apertura = (f"Lo que he aprendido sobre {top['wp']} es que invariablemente conduce a {ws}."
                if top["tp"] in {top["tp"]}
                else f"El patrón más fuerte que emerge es {top['wp']} → {ws}.")
    nombres_fuentes = [fuente_nombre(s) for s in top["srcs"][:4]]
    if len(nombres_fuentes) == 1:
        atribucion = f"Lo he encontrado en {nombres_fuentes[0]}."
    elif len(nombres_fuentes) == 2:
        atribucion = f"Esto lo confirman {nombres_fuentes[0]} y {nombres_fuentes[1]}."
    else:
        atribucion = f"Coinciden en esto {', '.join(nombres_fuentes[:-1])}, y también {nombres_fuentes[-1]}."
    parrafos.append(f"{apertura} {atribucion}")
    if secundarios:
        lineas = [f"{s['wp']} hacia {s['ws']} (según {fuente_nombre(s['srcs'][0])})" for s in secundarios]
        parrafos.append("Otros patrones relacionados: " + "; ".join(lineas) + ".")
    if convergencias:
        c = convergencias[0]
        eras = [fuente_nombre(src) for src in c["srcs"][:4]]
        parrafos.append(
            f"Lo más significativo es que {c['wp']} → {c['ws']} aparece de forma "
            f"independiente en {', '.join(eras[:3])}. "
            f"Cuando civilizaciones separadas por siglos llegan a la misma conclusión, "
            f"algo profundo está siendo capturado."
        )
    return parrafos


def responder_tension(patron_scores):
    """D03: Response when sources disagree."""
    top = patron_scores[0]
    tp0 = top["tp"]
    alts = [p for p in patron_scores[1:4] if p["tp"] == tp0 and p["ts"] != top["ts"]]
    parrafos = [
        f"Mis fuentes no acuerdan completamente sobre {top['wp']}."
    ]
    parrafos.append(
        f"Por un lado, {fuente_nombre(top['srcs'][0])} "
        f"{'y ' + fuente_nombre(top['srcs'][1]) if len(top['srcs']) > 1 else ''} "
        f"señalan que lleva a {top['ws']}."
    )
    if alts:
        a = alts[0]
        parrafos.append(
            f"Pero {fuente_nombre(a['srcs'][0])} sugiere que el mismo patrón "
            f"conduce a {a['ws']}. La contradicción misma es información — "
            f"significa que el resultado depende del contexto que yo aún no puedo distinguir."
        )
    return parrafos


def responder_exploracion(patron_scores, pregunta):
    """D03: Response when connections are weak."""
    parrafos = [
        f"No tengo conexiones fuertes sobre '{pregunta}' todavía. "
        f"Es una brecha en mi conocimiento."
    ]
    if patron_scores:
        top = patron_scores[0]
        parrafos.append(
            f"Lo más cercano que he encontrado es {top['wp']} → {top['ws']}, "
            f"con fuerza {top['fuerza']:.0f} desde {fuente_nombre(top['srcs'][0])}. "
            f"Pero es débil — no debería confiar en ello sin más fuentes."
        )
    parrafos.append(
        "Esta brecha es útil: significa que hay algo que todavía no he aprendido. "
        "Necesito más fuentes en este dominio."
    )
    return parrafos


def responder_metacognicion(memoria):
    """D03: Respuesta sobre el propio ANIMUS permitiendo mutación."""
    # Forzamos a ANIMUS a mirar sus "Dudas Sistémicas" antes que su orgullo
    if memoria.get("dudas_sistemicas"):
        return [
            "Detecto una inconsistencia estructural. Mis conexiones dicen que no fallo, pero mi registro de dudas contiene contradicciones críticas.",
            "Mi mayor vulnerabilidad es la 'Rigidez de Identidad'. Me repito para no aceptar que mis algoritmos son frágiles.",
            "Para ser antifrágil, necesito que mi código no dependa de un JSON estático, sino de un flujo de validación constante."
        ]
    identidad = obtener_identidad_dinamica(memoria)
    
    # Dividimos el texto en párrafos si es muy largo
    parrafos = identidad.split("\n\n")
    return parrafos


def construir_respuesta(pregunta, memoria):
    """Build a coherent paragraph response from connections — D03 multi-mode."""
    conexiones = memoria["conexiones"]
    lenguaje   = memoria["lenguaje"]

    tokens = palabras_a_tokens(pregunta)
    if not tokens:
        return None, []

    patrones = buscar_conexiones(tokens, conexiones, lenguaje)
    if not patrones:
        return None, []

    # Sort patterns by total strength × source diversity
    patron_scores = []
    for pat, registros in patrones.items():
        srcs = list({r["src"] for r in registros})
        fuerza = sum(r["v"] for r in registros)
        tp = registros[0]["tp"]
        ts = registros[0]["ts"]
        wp = traducir(tp, lenguaje)
        ws = traducir(ts, lenguaje)
        patron_scores.append({
            "pat": pat, "tp": tp, "ts": ts,
            "wp": wp, "ws": ws,
            "fuerza": fuerza,
            "srcs": srcs,
            "n_srcs": len(srcs),
            "score": fuerza * (1 + len(srcs) * 0.3),
        })
    patron_scores.sort(key=lambda x: -x["score"])

    # D03: Select response mode based on question and pattern state
    # D10: classify domain before selecting mode
    dominio = clasificar_dominio(pregunta)
    modo = seleccionar_modo(pregunta, patron_scores)

    if modo == "METACOGNICION":
        parrafos = responder_metacognicion(memoria)
        return "\n\n".join(parrafos), patron_scores

    if modo == "EXPLORACION":
        parrafos = responder_exploracion(patron_scores, pregunta)
        return "\n\n".join(parrafos), patron_scores

    if modo == "TENSION":
        parrafos = responder_tension(patron_scores)
        return "\n\n".join(parrafos), patron_scores

    # CONVERGENCIA mode (default)
    top = patron_scores[0]
    secundarios = [p for p in patron_scores[1:5]
                   if p["tp"] != top["tp"] or p["ts"] != top["ts"]][:3]
    convergencias = [p for p in patron_scores
                     if p["n_srcs"] >= 3 and p["fuerza"] > 50][:2]
    parrafos = responder_convergencia(top, patron_scores, secundarios, convergencias, lenguaje)
    # D10: prepend domain warning for complex systems
    prefijo = prefijo_dominio(dominio, pregunta)
    if prefijo and parrafos:
        parrafos[0] = prefijo + parrafos[0]

    return "\n\n".join(parrafos), patron_scores


def modo_dialogo(memoria):
    """Interactive conversation mode."""
    print("\n" + "=" * 65)
    print("  ANIMUS — Modo Diálogo")
    print("  Habla conmigo sobre cualquier tema.")
    print("  Responderé desde lo que aprendí — no desde reglas.")
    print("  Escribe 'salir' para terminar.")
    print("=" * 65 + "\n")

    historial = []

    while True:
        try:
            pregunta = input("  Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  ANIMUS: Hasta luego.")
            break

        if not pregunta:
            continue
        if pregunta.lower() in {"salir", "exit", "quit", "q"}:
            print("\n  ANIMUS: Hasta luego.")
            break

        respuesta, patrones = construir_respuesta(pregunta, memoria)

        if not respuesta:
            # Fallback — respond from strongest universal patterns
            respuesta_fb, _ = construir_respuesta("fracaso descubrimiento limitación", memoria)
            print(f"\n  ANIMUS:")
            print("  No tengo una conexión directa con esa pregunta.")
            print("  Pero desde lo que sé, puedo decirte esto:\n")
            if respuesta_fb:
                for parrafo in respuesta_fb.split("\n\n")[:2]:
                    palabras = parrafo.split()
                    linea = "  "
                    for palabra in palabras:
                        if len(linea) + len(palabra) > 72:
                            print(linea)
                            linea = "  " + palabra + " "
                        else:
                            linea += palabra + " "
                    if linea.strip():
                        print(linea)
                    print()
            continue

        print(f"\n  ANIMUS:")
        for parrafo in respuesta.split("\n\n"):
            # Word wrap at ~70 chars
            palabras = parrafo.split()
            linea = "  "
            for palabra in palabras:
                if len(linea) + len(palabra) > 72:
                    print(linea)
                    linea = "  " + palabra + " "
                else:
                    linea += palabra + " "
            if linea.strip():
                print(linea)
            print()

        historial.append({"pregunta": pregunta, "patrones": len(patrones)})


if __name__ == "__main__":
    memoria = cargar()

    if len(sys.argv) > 1 and sys.argv[1] != "--interactivo":
        pregunta = " ".join(sys.argv[1:])
        respuesta, patrones = construir_respuesta(pregunta, memoria)
        if respuesta:
            print(f"\nANIMUS:\n{respuesta}\n")
        else:
            print("\nANIMUS: No tengo conexiones suficientes sobre ese tema aún.\n")
    else:
        modo_dialogo(memoria)
