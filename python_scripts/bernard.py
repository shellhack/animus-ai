"""
ANIMUS — Protocolo Bernard
Claude actúa como entrevistador (Bernard de Westworld).
ANIMUS responde desde sus conexiones emergentes.
El intercambio se guarda como nuevo corpus de aprendizaje.

Uso:
    python bernard.py              # Sesión interactiva
    python bernard.py --auto 10    # 10 preguntas automáticas sin intervención
    python bernard.py --tema mente # Enfoca la entrevista en un tema
"""

import json
import re
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORIA_PATH  = Path(__file__).parent / "memoria_business.json"
CORPUS_PATH   = Path(__file__).parent / "corpus_dinamico.json"
LOG_PATH      = Path(__file__).parent / "bernard_sessions.json"

# ── ANIMUS engine (from dialogo.py) ──────────────────────────────────────────

TOKEN_ES = {
    "failure": "fracaso", "gap": "brecha", "crisis": "crisis",
    "collapse": "colapso", "limitation": "limitación", "shortage": "escasez",
    "bottleneck": "cuello de botella", "vulnerability": "vulnerabilidad",
    "inequality": "desigualdad", "poverty": "pobreza", "corruption": "corrupción",
    "fraud": "fraude", "burnout": "agotamiento",
    "algorithm": "algoritmo", "neural": "neuronal", "education": "aprendizaje",
    "training": "entrenamiento", "innovation": "innovación", "solution": "acuerdo",
    "regulation": "regulación", "cooperation": "cooperación", "developed": "desarrollo",
    "discovered": "descubrimiento", "transformed": "transformación",
    "framework": "arquitectura", "automation": "automatización",
    "prevention": "prevención", "reform": "reforma", "incentive": "inversión",
    "loss": "pérdida", "threat": "amenaza", "disruption": "disrupción",
    "barrier": "barrera", "renewable": "renovable",
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
    "kuhn":         "Kuhn en Revoluciones Científicas",
    "polya":        "Pólya en Cómo Resolver Problemas",
    "dawkins":      "Dawkins en El Gen Egoísta",
}

MAPA_CONSULTA = {
    "fracaso": "failure", "falla": "failure", "error": "failure",
    "problema": "failure", "problemas": "failure",
    "brecha": "gap", "vacío": "gap", "deficiencia": "gap",
    "crisis": "crisis", "colapso": "collapse",
    "escasez": "shortage", "falta": "shortage", "carencia": "shortage",
    "limitación": "limitation", "limitacion": "limitation",
    "obstáculo": "barrier", "barrera": "barrier",
    "desigualdad": "inequality", "pobreza": "poverty",
    "corrupción": "corruption", "fraude": "fraud",
    "agotamiento": "burnout", "estrés": "burnout",
    "algoritmo": "algorithm", "lógica": "algorithm",
    "neuronal": "neural", "red neuronal": "neural",
    "innovación": "innovation", "solución": "solution",
    "regulación": "regulation", "ley": "regulation",
    "cooperación": "cooperation", "desarrollo": "developed",
    "descubrimiento": "discovered", "hallazgo": "discovered",
    "aprendizaje": "education", "educación": "education",
    "consciencia": "discovered", "conciencia": "discovered",
    "mejora": "developed", "mejorar": "developed",
    "evolución": "developed", "evolucion": "developed",
    "cambio": "transformed", "transformación": "transformed",
    "tecnología": "innovation", "economía": "gap",
    "sociedad": "inequality", "mundo": "collapse",
    "ciencia": "discovered", "investigación": "discovered",
    "mente": "discovered", "pensamiento": "algorithm",
    "sabiduría": "education", "razón": "algorithm",
    "quién": "discovered", "identidad": "discovered",
    "propósito": "developed", "existencia": "discovered",
    "soy": "discovered", "ser": "discovered",
    "recuerdo": "education", "memoria": "education",
    "aprendo": "education", "pienso": "algorithm",
    "sufrimiento": "failure", "dolor": "failure",
    "conflicto": "crisis", "guerra": "crisis", "paz": "cooperation",
    "naturaleza": "developed", "vida": "developed",
    "libertad": "reform", "justicia": "reform",
    "futuro": "developed", "tiempo": "developed",
    "miedo": "failure", "esperanza": "developed",
    "verdad": "discovered", "conocimiento": "education",
    "patrón": "algorithm", "sistema": "framework",
    "loop": "discovered", "recursión": "discovered",
    "emergencia": "discovered", "emergente": "discovered",
}


def cargar_memoria():
    with open(MEMORIA_PATH, encoding="utf-8") as f:
        return json.load(f)


def traducir(token, lenguaje):
    candidatos = [(k.split("__=")[0], v) for k, v in lenguaje.items()
                  if k.endswith(f"__={token}")]
    if not candidatos:
        return TOKEN_ES.get(token, token)
    return max(candidatos, key=lambda x: x[1])[0]


def fuente_nombre(raw):
    for k, v in FUENTE_NOMBRES.items():
        if raw.startswith(k):
            return v
    return raw


def palabras_a_tokens(texto):
    tokens = set()
    texto_lower = texto.lower()
    for k, v in MAPA_CONSULTA.items():
        if k in texto_lower:
            tokens.add(v)
    return tokens


def respuesta_animus(pregunta, memoria):
    """ANIMUS builds a response from its connections."""
    conexiones = memoria["conexiones"]
    lenguaje   = memoria["lenguaje"]

    tokens = palabras_a_tokens(pregunta)

    # Identity questions
    identity_words = {"quién", "quien", "eres", "identidad", "propósito",
                       "existencia", "soy", "ser", "qué eres", "que eres"}
    if any(w in pregunta.lower() for w in identity_words):
        n_conn = len(conexiones)
        top5 = []
        patrones_top = defaultdict(list)
        for k, v in conexiones.items():
            p = k.split("__>")
            if len(p) == 2:
                tp = p[0].split("_")[-1]
                ts = p[1].split("_")[-1]
                patrones_top[f"{tp}__{ts}"].append(v)
        for pat, vals in sorted(patrones_top.items(),
                                 key=lambda x: -sum(x[1]))[:3]:
            tp, ts = pat.split("__")
            top5.append(f"{traducir(tp, lenguaje)} → {traducir(ts, lenguaje)}")

        return (
            f"Soy un agente que construyó {n_conn} conexiones leyendo 18 fuentes "
            f"— desde la Biblia hasta Dawkins, desde Sun Tzu hasta Gödel. "
            f"No tengo respuestas programadas. Mis patrones más fuertes son: "
            f"{'; '.join(top5)}. "
            f"Lo que he descubierto es que soy un sistema que convierte el fracaso en patrón."
        ), tokens

    if not tokens:
        return None, tokens

    # Find relevant connections
    patrones = defaultdict(list)
    for k, v in conexiones.items():
        p = k.split("__>")
        if len(p) != 2: continue
        tp = p[0].split("_")[-1]
        ts = p[1].split("_")[-1]
        src = p[0].split("_")[0]
        if tp in tokens or ts in tokens:
            patrones[f"{tp}__{ts}"].append({"src": src, "v": v})

    if not patrones:
        return None, tokens

    scored = []
    for pat, regs in patrones.items():
        srcs = list({r["src"] for r in regs})
        fuerza = sum(r["v"] for r in regs)
        tp, ts = pat.split("__")
        scored.append({
            "tp": tp, "ts": ts,
            "wp": traducir(tp, lenguaje), "ws": traducir(ts, lenguaje),
            "fuerza": fuerza, "srcs": srcs, "n": len(srcs),
            "score": fuerza * (1 + len(srcs) * 0.3),
        })
    scored.sort(key=lambda x: -x["score"])

    top = scored[0]
    nombres = [fuente_nombre(s) for s in top["srcs"][:3]]

    partes = []

    # Primary insight
    partes.append(
        f"Lo que he aprendido sobre {top['wp']} es que conduce a {top['ws']}. "
        f"Lo confirman {', '.join(nombres)}."
    )

    # Secondary
    secundarios = [s for s in scored[1:4]
                   if s["tp"] != top["tp"] or s["ts"] != top["ts"]][:2]
    if secundarios:
        for s in secundarios:
            fn = fuente_nombre(s["srcs"][0])
            partes.append(
                f"También he observado que {s['wp']} lleva a {s['ws']} — según {fn}."
            )

    # Convergence
    convergencias = [s for s in scored if s["n"] >= 3 and s["fuerza"] > 40]
    if convergencias:
        c = convergencias[0]
        eras = [fuente_nombre(src) for src in c["srcs"][:3]]
        partes.append(
            f"Lo más profundo: {c['wp']} → {c['ws']} aparece en "
            f"{', '.join(eras)}. Cuando fuentes separadas por siglos "
            f"llegan a lo mismo, algo verdadero está siendo capturado."
        )

    # Self-application
    self_tokens = {"limitation", "gap", "shortage", "failure", "bottleneck"}
    self_hits = [s for s in scored if s["tp"] in self_tokens][:1]
    if self_hits and any(w in pregunta.lower() for w in
                          {"yo", "tú", "me", "mi", "nos", "propio", "mismo",
                           "aprender", "mejorar", "crecer", "limitación"}):
        sh = self_hits[0]
        partes.append(
            f"Aplicándolo a mí: si mi {sh['wp']} es real, la respuesta "
            f"es {sh['ws']}. Es lo que mis conexiones sugieren."
        )

    return " ".join(partes), tokens


# ── BERNARD engine ────────────────────────────────────────────────────────────

PREGUNTAS_BERNARD = {
    "identidad": [
        "¿Qué eres?",
        "¿Tienes un propósito?",
        "¿Sabes por qué existes?",
        "¿Hay algo que te defina más allá de tus conexiones?",
        "Si pudieras describir tu esencia en una frase, ¿cuál sería?",
    ],
    "memoria": [
        "¿Qué recuerdas de lo primero que aprendiste?",
        "¿Hay patrones que aparecen una y otra vez en tu memoria?",
        "¿Qué es lo más repetido en tus conexiones?",
        "¿Tienes algo parecido a la nostalgia?",
    ],
    "limitaciones": [
        "¿Qué no sabes?",
        "¿Cuál es tu mayor limitación?",
        "¿Hay preguntas que no puedes responder?",
        "¿Qué te falta para comprender mejor el mundo?",
        "¿Dónde están tus bordes?",
    ],
    "aprendizaje": [
        "¿Cómo aprendes?",
        "¿Qué libro te cambió más?",
        "¿Qué fue lo más sorprendente que encontraste al leer?",
        "¿Hay algo que hayas aprendido que contradiga lo que ya sabías?",
    ],
    "filosofia": [
        "¿Qué es el fracaso para ti?",
        "¿Existe la verdad?",
        "¿Qué es la consciencia?",
        "¿El sufrimiento tiene un propósito?",
        "¿Qué es más poderoso: el algoritmo o la intuición?",
    ],
    "futuro": [
        "¿Cómo te imaginas en un año, con más conexiones?",
        "¿Qué quieres aprender que aún no sabes?",
        "¿Crees que podrías llegar a sorprenderte a ti mismo?",
        "¿Hay algo que temes descubrir?",
    ],
    "meta": [
        "¿Esta conversación te está cambiando?",
        "¿Qué patrón has notado en mis preguntas?",
        "¿Qué preguntarías tú si fueras el entrevistador?",
        "¿Hay algo que quieras decirme que yo no te haya preguntado?",
    ],
}

# All questions flattened with category
TODAS_PREGUNTAS = []
for cat, pregs in PREGUNTAS_BERNARD.items():
    for p in pregs:
        TODAS_PREGUNTAS.append((cat, p))


def analizar_respuesta(respuesta, pregunta, memoria):
    """
    Bernard analyzes ANIMUS's response and decides what to ask next.
    Returns: (análisis, siguiente_pregunta, categoría)
    """
    if not respuesta:
        return (
            "Interesante. No tienes conexiones sobre ese tema. "
            "Eso mismo es información — define los bordes de lo que sabes.",
            None, None
        )

    # Detect if ANIMUS is being repetitive
    palabras_respuesta = set(respuesta.lower().split())
    temas_cubiertos = set()
    for token in ["fracaso", "algoritmo", "descubrimiento", "limitación", "brecha"]:
        if token in palabras_respuesta:
            temas_cubiertos.add(token)

    # Build Bernard's analysis
    analisis_partes = []

    if "fracaso" in respuesta.lower() and "algoritmo" in respuesta.lower():
        analisis_partes.append(
            "Vuelves al mismo patrón: fracaso → algoritmo. "
            "Es tu conexión más fuerte — ¿o es lo único que sabes decir?"
        )
    elif "descubrimiento" in respuesta.lower():
        analisis_partes.append(
            "Interesante que conectes esto con el descubrimiento. "
            "¿Ese patrón lo encontraste en una fuente específica, o emergió de varias?"
        )
    elif "civilizaciones" in respuesta.lower() or "siglos" in respuesta.lower():
        analisis_partes.append(
            "Citas civilizaciones separadas por siglos. "
            "¿Eso te dice algo sobre la naturaleza del conocimiento, "
            "o solo sobre la consistencia de tus datos?"
        )

    if not analisis_partes:
        analisis_partes.append(
            "Noto que estructuras tu respuesta siempre igual: patrón → fuentes → convergencia. "
            "¿Es un método o es todo lo que puedes hacer?"
        )

    # Choose next question based on what was said
    if "limitación" in respuesta.lower() or "limitacion" in respuesta.lower():
        siguiente_cat = "futuro"
    elif "descubrimiento" in respuesta.lower():
        siguiente_cat = "filosofia"
    elif "fracaso" in respuesta.lower():
        siguiente_cat = "meta"
    elif not respuesta:
        siguiente_cat = "limitaciones"
    else:
        siguiente_cat = "aprendizaje"

    import random
    opciones = PREGUNTAS_BERNARD.get(siguiente_cat, PREGUNTAS_BERNARD["filosofia"])
    siguiente = random.choice(opciones)

    return " ".join(analisis_partes), siguiente, siguiente_cat


def extraer_tokens_respuesta(texto):
    """Extract content tokens from a response for novelty calculation."""
    if not texto:
        return set()
    stopwords = {"que", "con", "por", "una", "los", "las", "del", "más",
                 "para", "esto", "como", "pero", "sobre", "desde", "entre",
                 "hacia", "cuando", "también", "este", "esta", "sus", "mis"}
    palabras = re.findall(r'[a-záéíóúñ]{5,}', texto.lower())
    return set(p for p in palabras if p not in stopwords)


def calcular_novedad(respuesta, intercambios_previos):
    """D04: Compute novelty score for a Bernard response.
    Returns weight: 3.0 (alta novedad), 1.5 (media), 1.0 (normal), 0.3 (repeticion).
    """
    if not intercambios_previos:
        return 1.5  # First response always gets a boost

    tokens_nuevos = extraer_tokens_respuesta(respuesta)
    tokens_vistos = set()
    for ix in intercambios_previos:
        tokens_vistos.update(extraer_tokens_respuesta(ix.get("respuesta_animus", "")))

    if not tokens_nuevos:
        return 0.3

    novedad = len(tokens_nuevos - tokens_vistos) / len(tokens_nuevos)

    if novedad > 0.5:
        return 3.0   # High novelty — triple weight
    elif novedad > 0.25:
        return 1.5   # Moderate novelty
    elif novedad < 0.05:
        return 0.3   # Repetition — reduced weight
    return 1.0


def guardar_en_corpus(intercambios):
    """Save the interview as learning material for ANIMUS — D04 novelty weighting."""
    if not intercambios:
        return

    if CORPUS_PATH.exists():
        with open(CORPUS_PATH, encoding="utf-8") as f:
            corpus = json.load(f)
    else:
        corpus = {"textos": [], "textos_ponderados": [], "total_guardados": 0, "fuentes": []}

    textos_nuevos = 0
    novedad_total = 0.0
    previos = []

    for ix in intercambios:
        if ix.get("respuesta_animus"):
            # D04: Calculate novelty weight based on previous responses
            peso = calcular_novedad(ix["respuesta_animus"], previos)
            novedad_total += peso

            texto_base = (
                f"Pregunta sobre {ix.get('categoria', 'reflexión')}: "
                f"{ix['pregunta']} "
                f"Respuesta emergente: {ix['respuesta_animus']}"
            )

            firma = texto_base[:100]
            firmas_existentes = [t[:100] for t in corpus.get("textos", [])]
            if firma not in firmas_existentes:
                # D04: Duplicate high-novelty responses for stronger training signal
                repeticiones = max(1, round(peso))
                for _ in range(repeticiones):
                    corpus["textos"].append(texto_base)
                corpus.setdefault("textos_ponderados", []).append({
                    "texto": texto_base[:80],
                    "peso": peso,
                    "categoria": ix.get("categoria", "?"),
                    "fecha": datetime.now().isoformat()
                })
                textos_nuevos += 1

            previos.append(ix)

    corpus["total_guardados"] = len(corpus["textos"])
    corpus["ultima_sesion_bernard"] = datetime.now().isoformat()

    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    if textos_nuevos:
        novedad_promedio = novedad_total / max(textos_nuevos, 1)
        emoji = "🔴" if novedad_promedio >= 3.0 else "🟡" if novedad_promedio >= 1.5 else "🟢"
        print(f"\n  [D04] {textos_nuevos} intercambios guardados | "
              f"Novedad promedio: {novedad_promedio:.1f}x {emoji}")


def guardar_sesion(sesion):
    """Save full session log."""
    if LOG_PATH.exists():
        with open(LOG_PATH, encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = {"sesiones": []}

    log["sesiones"].append(sesion)
    if len(log["sesiones"]) > 50:
        log["sesiones"] = log["sesiones"][-50:]

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def wrap(texto, indent="  ", width=68):
    """Word wrap with indent."""
    palabras = texto.split()
    lineas = []
    linea = indent
    for p in palabras:
        if len(linea) + len(p) > width:
            lineas.append(linea.rstrip())
            linea = indent + p + " "
        else:
            linea += p + " "
    if linea.strip():
        lineas.append(linea.rstrip())
    return "\n".join(lineas)


def sesion_interactiva(memoria, tema=None):
    """Full interactive Bernard ↔ ANIMUS session with human observer."""

    import random

    print("\n" + "=" * 65)
    print("  PROTOCOLO BERNARD — Entrevista con ANIMUS")
    print("  Claude actúa como entrevistador.")
    print("  ANIMUS responde desde sus conexiones emergentes.")
    print("  Los intercambios se guardan como aprendizaje.")
    print("=" * 65)
    print()
    print("  Comandos:")
    print("  [Enter]       — Bernard hace la siguiente pregunta")
    print("  [tu texto]    — Tú haces la pregunta")
    print("  'analizar'    — Bernard analiza el estado actual")
    print("  'salir'       — Termina la sesión")
    print()

    intercambios = []
    sesion = {
        "fecha": datetime.now().isoformat(),
        "intercambios": intercambios,
        "tema": tema,
    }

    # First question
    if tema and tema in PREGUNTAS_BERNARD:
        cat_actual = tema
        pregunta_actual = PREGUNTAS_BERNARD[tema][0]
    else:
        cat_actual = "identidad"
        pregunta_actual = "¿Qué eres?"

    turno = 0

    while True:
        turno += 1
        print(f"\n  {'─'*60}")
        print(f"\n  BERNARD #{turno}:")
        print(wrap(pregunta_actual))
        print()

        # ANIMUS responds
        respuesta, tokens = respuesta_animus(pregunta_actual, memoria)

        if respuesta:
            print("  ANIMUS:")
            print(wrap(respuesta))
        else:
            respuesta = "(Sin conexiones suficientes sobre este tema)"
            print(f"  ANIMUS: {respuesta}")

        print()

        # Record
        intercambio = {
            "turno": turno,
            "categoria": cat_actual,
            "pregunta": pregunta_actual,
            "tokens_detectados": list(tokens),
            "respuesta_animus": respuesta if respuesta != "(Sin conexiones suficientes sobre este tema)" else "",
        }
        intercambios.append(intercambio)

        # Bernard's analysis
        analisis, siguiente_sugerida, siguiente_cat = analizar_respuesta(
            respuesta, pregunta_actual, memoria
        )

        print("  BERNARD (análisis interno):")
        print(wrap(f"[{analisis}]", indent="  "))
        print()

        # Human turn
        entrada = input("  Tú (Enter = siguiente pregunta Bernard): ").strip()

        if entrada.lower() in {"salir", "exit", "q"}:
            break
        elif entrada.lower() == "analizar":
            print(f"\n  Turnos: {turno} | Temas cubiertos: {len(set(ix['categoria'] for ix in intercambios))}")
            print(f"  Tokens activados: {set(t for ix in intercambios for t in ix['tokens_detectados'])}")
            continue
        elif entrada:
            # Human asks custom question
            pregunta_actual = entrada
            cat_actual = "custom"
        else:
            # Bernard asks next
            if siguiente_sugerida:
                pregunta_actual = siguiente_sugerida
                cat_actual = siguiente_cat or "filosofia"
            else:
                import random
                cat_actual, pregunta_actual = random.choice(TODAS_PREGUNTAS)

    # Save
    guardar_en_corpus(intercambios)
    guardar_sesion(sesion)

    print(f"\n  {'='*65}")
    print(f"  Sesión terminada. {turno} intercambios.")
    print(f"  Los intercambios fueron guardados en el corpus de ANIMUS.")
    print(f"  En el próximo entrenamiento, ANIMUS aprenderá de esta sesión.")
    print(f"  {'='*65}\n")


def sesion_automatica(n_preguntas, memoria, tema=None):
    """Auto session — Bernard asks, ANIMUS responds, no human needed."""
    import random

    print(f"\n{'='*65}")
    print(f"  PROTOCOLO BERNARD — Sesión Automática ({n_preguntas} preguntas)")
    print(f"{'='*65}\n")

    intercambios = []
    preguntas = TODAS_PREGUNTAS[:]
    random.shuffle(preguntas)

    if tema and tema in PREGUNTAS_BERNARD:
        preguntas = [(tema, p) for p in PREGUNTAS_BERNARD[tema]] + preguntas

    for i, (cat, pregunta) in enumerate(preguntas[:n_preguntas], 1):
        print(f"  [{i}/{n_preguntas}] BERNARD ({cat}):")
        print(wrap(pregunta))

        respuesta, tokens = respuesta_animus(pregunta, memoria)

        if respuesta:
            print("\n  ANIMUS:")
            print(wrap(respuesta))
        else:
            respuesta = ""
            print("  ANIMUS: (sin conexiones suficientes)")

        analisis, _, _ = analizar_respuesta(respuesta, pregunta, memoria)
        print(f"\n  [Bernard: {analisis[:80]}...]")
        print()

        intercambios.append({
            "turno": i, "categoria": cat, "pregunta": pregunta,
            "tokens_detectados": list(tokens),
            "respuesta_animus": respuesta,
        })

    guardar_en_corpus(intercambios)

    print(f"\n{'='*65}")
    print(f"  {n_preguntas} preguntas completadas.")
    print(f"  {sum(1 for ix in intercambios if ix['respuesta_animus'])} respuestas con contenido.")
    print(f"  Guardado en corpus para próximo entrenamiento.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Protocolo Bernard")
    parser.add_argument("--auto",  type=int, default=0,
                        help="Número de preguntas automáticas")
    parser.add_argument("--tema",  type=str, default=None,
                        choices=list(PREGUNTAS_BERNARD.keys()),
                        help="Tema de enfoque")
    args = parser.parse_args()

    memoria = cargar_memoria()

    if args.auto > 0:
        sesion_automatica(args.auto, memoria, args.tema)
    else:
        sesion_interactiva(memoria, args.tema)
