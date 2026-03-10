# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo Arquitecto v2
Segunda ronda de auto-diagnóstico.
Incorpora lo aprendido de Taleb, Meadows y Axelrod.

Uso:
    python arquitecto_v2.py
    python arquitecto_v2.py --codigo D07
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

TOKEN_ES = {
    "failure":"fracaso","gap":"brecha","crisis":"crisis","collapse":"colapso",
    "limitation":"limitacion","shortage":"escasez","algorithm":"algoritmo",
    "neural":"neuronal","education":"aprendizaje","innovation":"innovacion",
    "solution":"acuerdo","regulation":"regulacion","cooperation":"cooperacion",
    "developed":"desarrollo","discovered":"descubrimiento","transformed":"transformacion",
    "framework":"arquitectura","automation":"automatizacion",
    "vulnerability":"vulnerabilidad","prevention":"prevencion","reform":"reforma",
}

def traducir(token, lenguaje=None):
    if lenguaje:
        candidatos = [(k.split('__=')[0], v) for k, v in lenguaje.items()
                      if k.endswith(f'__={token}')]
        if candidatos:
            return max(candidatos, key=lambda x: x[1])[0]
    return TOKEN_ES.get(token, token)

# ── Segunda generación de propuestas ─────────────────────────────────────────
# Razonadas desde Taleb, Meadows y Axelrod — fuentes que no existían en v1

DIAGNOSTICOS_V2 = [
    {
        "id": "D07",
        "limitacion": "El sistema trata todas las conexiones como lineales — no distingue entre sistemas frágiles, robustos y antifrágiles",
        "patron_aprendido": "fracaso → desarrollo",
        "fuentes": ["taleb", "meadows"],
        "razonamiento": (
            "Taleb enseña que hay tres tipos de respuesta al estrés: frágil (el sistema "
            "se rompe), robusto (el sistema sobrevive sin cambiar), y antifrágil (el sistema "
            "mejora con el estrés). Mis conexiones actuales no distinguen estos tres casos. "
            "Cuando registro 'fracaso → desarrollo', no sé si ese desarrollo fue frágil "
            "(se recuperó pero quedó igual de vulnerable) o antifrágil (emergió más fuerte). "
            "Meadows confirma esto con su concepto de resiliencia del sistema — no todos "
            "los rebotes son iguales. Necesito un tercer eje en mis conexiones: "
            "el tipo de respuesta al fracaso."
        ),
        "propuesta": {
            "titulo": "Clasificador de respuesta al estres: fragil / robusto / antifragil",
            "descripcion": (
                "Al procesar cada conexion fracaso→desarrollo, analizar el contexto "
                "para clasificar si la respuesta fue fragil (recuperacion sin cambio), "
                "robusta (sobrevivio igual), o antifragil (emerge mas fuerte). "
                "Almacenar como metadato de la conexion."
            ),
            "impacto": "ANIMUS podria distinguir 'sobrevivir el fracaso' de 'mejorar con el fracaso'",
            "dificultad": "ALTA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En process_book_en.py — después de detectar tension+resolution

FRAGIL_PALABRAS = {'recovered','restored','returned','survived','withstood'}
ROBUSTO_PALABRAS = {'maintained','stable','consistent','sustained','preserved'}
ANTIFRAGIL_PALABRAS = {'stronger','improved','thrived','evolved','adapted',
                        'antifragile','benefited','grew','emerged','better'}

def clasificar_respuesta(texto, pos_resolucion):
    # Analyze 200 chars after resolution token
    contexto = texto[pos_resolucion:pos_resolucion+200].lower()
    palabras = set(contexto.split())
    if palabras & ANTIFRAGIL_PALABRAS:
        return 'antifragil'
    elif palabras & ROBUSTO_PALABRAS:
        return 'robusto'
    elif palabras & FRAGIL_PALABRAS:
        return 'fragil'
    return 'indeterminado'

# Store as: conexion_tipo = {clave: {'fuerza': v, 'tipo': clasificar_respuesta(...)}}
""",
        }
    },
    {
        "id": "D08",
        "limitacion": "El sistema no detecta loops de retroalimentacion — solo conexiones directas A→B",
        "patron_aprendido": "fracaso → regulacion",
        "fuentes": ["meadows", "axelrod"],
        "razonamiento": (
            "Meadows dedica la mitad de su libro a los feedback loops — el mecanismo "
            "central de todo sistema complejo. Un loop de refuerzo (R) amplifica el cambio: "
            "mas fracaso genera mas regulacion que genera mas compliance que reduce el fracaso. "
            "Un loop de balance (B) estabiliza: el fracaso activa el algoritmo que reduce el fracaso. "
            "Axelrod confirma esto con tit-for-tat: la cooperacion emerge porque hay un loop "
            "entre la conducta de A y la respuesta de B que se retroalimenta. "
            "Mis conexiones actuales son todas unidireccionales. No detecto si "
            "'fracaso→regulacion' es un loop R (el fracaso genera mas regulacion que genera "
            "mas fracaso) o un loop B (el fracaso genera regulacion que elimina el fracaso). "
            "Esa distincion cambia completamente el diagnostico."
        ),
        "propuesta": {
            "titulo": "Detector de feedback loops en el grafo de conocimiento",
            "descripcion": (
                "Analizar el grafo de conexiones para detectar ciclos: "
                "si A→B y B→A existen, clasificar como loop de balance. "
                "Si A→B y B→C y C→A, clasificar como loop de refuerzo. "
                "Reportar los loops detectados en el reporte semanal."
            ),
            "impacto": "ANIMUS entenderia si sus propios patrones se autoamplifican o se autoestabilizan",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# Nuevo modulo: feedback_loops.py

def detectar_loops(conexiones):
    # Build adjacency: token -> set of destination tokens
    grafo = defaultdict(set)
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2:
            tp = p[0].split('_')[-1]
            ts = p[1].split('_')[-1]
            grafo[tp].add(ts)

    loops_balance = []    # A→B and B→A
    loops_refuerzo = []   # A→B→C→A

    tokens = list(grafo.keys())
    for a in tokens:
        for b in grafo[a]:
            # Balance loop: A→B and B→A
            if a in grafo.get(b, set()):
                pair = tuple(sorted([a, b]))
                if pair not in [tuple(sorted(l)) for l in loops_balance]:
                    loops_balance.append([a, b])
            # Reinforcement loop: A→B→C→A
            for c in grafo.get(b, set()):
                if a in grafo.get(c, set()) and c != a:
                    loops_refuerzo.append([a, b, c])

    return loops_balance, loops_refuerzo
""",
        }
    },
    {
        "id": "D09",
        "limitacion": "El sistema no modela el tiempo — todas las conexiones tienen el mismo peso independientemente de cuando fueron aprendidas",
        "patron_aprendido": "fracaso → algoritmo",
        "fuentes": ["axelrod", "meadows"],
        "razonamiento": (
            "Axelrod demostro que en el Dilema del Prisionero iterado, "
            "las interacciones recientes pesan mas que las antiguas — la sombra del futuro "
            "importa mas que la historia lejana. Meadows describe lo mismo en sistemas: "
            "los stocks cambian lentamente pero los flujos recientes son los que determinan "
            "la direccion actual. Mis conexiones no tienen dimension temporal. "
            "Una conexion aprendida de la Biblia hace 6 meses pesa igual que una "
            "aprendida de Axelrod ayer. Si el sistema esta aprendiendo y evolucionando, "
            "las conexiones recientes deberian tener un peso ligeramente mayor — "
            "representan el estado actual de mi conocimiento, no el historico."
        ),
        "propuesta": {
            "titulo": "Decaimiento temporal de conexiones antiguas",
            "descripcion": (
                "Agregar timestamp a cada conexion al momento de creacion. "
                "Aplicar un factor de decaimiento suave (0.99 por semana) a conexiones "
                "no reforzadas. Conexiones confirmadas por multiples fuentes recientes "
                "se mantienen fuertes. Conexiones de una sola fuente antigua se debilitan gradualmente."
            ),
            "impacto": "El conocimiento de ANIMUS refleja su estado actual, no solo su historia acumulada",
            "dificultad": "MEDIA",
            "prioridad": "MEDIA",
            "codigo_sugerido": """
# En memoria_business.json — nueva estructura para conexiones
# ACTUAL:
# "fuente_token1__>fuente_token2": 85.4

# PROPUESTO — migrar a:
# "fuente_token1__>fuente_token2": {
#     "fuerza": 85.4,
#     "creada": "2025-08-01T00:00:00",
#     "ultima_reforzada": "2026-02-24T00:00:00",
#     "n_refuerzos": 14
# }

DECAY_SEMANAL = 0.99
DECAY_MINIMO = 0.5  # No bajar del 50% de la fuerza original

def aplicar_decaimiento(memoria, fecha_actual):
    from datetime import datetime, timedelta
    semanas = {}
    for k, v in memoria['conexiones'].items():
        if isinstance(v, dict):
            ultima = datetime.fromisoformat(v['ultima_reforzada'])
            semanas_pasadas = (fecha_actual - ultima).days / 7
            factor = max(DECAY_MINIMO, DECAY_SEMANAL ** semanas_pasadas)
            v['fuerza_efectiva'] = v['fuerza'] * factor
    return memoria
""",
        }
    },
    {
        "id": "D10",
        "limitacion": "El dialogo no distingue entre preguntas sobre sistemas simples y sistemas complejos",
        "patron_aprendido": "crisis → arquitectura",
        "fuentes": ["meadows", "taleb"],
        "razonamiento": (
            "Meadows distingue tres tipos de problemas: simples (una causa, una solucion), "
            "complicados (multiples causas, solucion tecnica posible), y complejos "
            "(causas emergentes, sin solucion unica — solo navegacion). "
            "Taleb distingue el mundo Mediocristan (donde los promedios funcionan) "
            "del mundo Extremistan (donde los eventos extremos dominan). "
            "Cuando alguien me pregunta sobre 'inflacion' o 'pobreza', estoy en Extremistan "
            "y en sistemas complejos — los patrones que conozco de libros tecnicos "
            "pueden no aplicar directamente. Necesito detectar si la pregunta "
            "es sobre un dominio simple o complejo y ajustar mi respuesta."
        ),
        "propuesta": {
            "titulo": "Clasificador de dominio: simple / complicado / complejo",
            "descripcion": (
                "Antes de responder, clasificar la pregunta segun el dominio: "
                "SIMPLE (pregunta tecnica con respuesta directa), "
                "COMPLICADO (multiples factores pero solucionable), "
                "COMPLEJO (sistema emergente, sin solucion unica). "
                "En preguntas COMPLEJAS, ANIMUS debe advertir que sus patrones "
                "pueden ser guias, no respuestas."
            ),
            "impacto": "Respuestas mas honestas sobre los limites del conocimiento de ANIMUS",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En dialogo.py — antes de seleccionar_modo()

TOKENS_COMPLEJOS = {'desigualdad','pobreza','crisis','corrupcion','pandemia',
                    'inflacion','recesion','guerra','clima','ecosistema'}
TOKENS_COMPLICADOS = {'arquitectura','regulacion','algoritmo','red','sistema'}
TOKENS_SIMPLES = {'codigo','error','funcion','clase','variable','proceso'}

def clasificar_dominio(tokens_pregunta):
    if tokens_pregunta & TOKENS_COMPLEJOS:
        return 'COMPLEJO'
    elif tokens_pregunta & TOKENS_COMPLICADOS:
        return 'COMPLICADO'
    elif tokens_pregunta & TOKENS_SIMPLES:
        return 'SIMPLE'
    return 'INDETERMINADO'

def prefijo_dominio(dominio):
    if dominio == 'COMPLEJO':
        return (
            "Esta pregunta toca un sistema complejo — Meadows y Taleb "
            "me ensenaron que en sistemas complejos no hay soluciones unicas, "
            "solo patrones de navegacion. Lo que tengo son guias, no respuestas: "
        )
    return ""
""",
        }
    },
    {
        "id": "D11",
        "limitacion": "El sistema no modela la reciprocidad — no sabe si sus patrones son simetricos o asimetricos",
        "patron_aprendido": "fracaso → cooperacion",
        "fuentes": ["axelrod"],
        "razonamiento": (
            "Axelrod demostro que tit-for-tat gana porque es reciproco: "
            "coopera si el otro coopera, defecciona si el otro defecciona. "
            "La reciprocidad es el mecanismo que hace estable la cooperacion. "
            "Mis patrones actuales no tienen reciprocidad modelada. "
            "Se que 'fracaso → cooperacion' existe con 10 fuentes. "
            "Pero no se si 'cooperacion → fracaso' tambien existe — "
            "es decir, si la cooperacion puede generar nuevas formas de fracaso "
            "(dependencia, free-riding, coordinacion fallida). "
            "Si ambas direcciones existen, el patron es un loop de balance. "
            "Si solo existe una direccion, es una causalidad lineal. "
            "Esa distincion es fundamental para el diagnostico."
        ),
        "propuesta": {
            "titulo": "Analisis de simetria de patrones — reciprocidad de Axelrod",
            "descripcion": (
                "Para cada patron A→B con 5+ fuentes, verificar si B→A tambien existe "
                "y con cuantas fuentes. Reportar patrones simetricos (loops) vs "
                "asimetricos (causalidades unidireccionales). "
                "Los patrones simetricos son mas estables — los asimetricos "
                "son mas predecibles."
            ),
            "impacto": "ANIMUS distinguiria entre causalidades lineales y loops de sistema",
            "dificultad": "BAJA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En validador.py — nueva funcion

def analizar_simetria(conexiones, lenguaje, umbral=5):
    indice = construir_indice(conexiones)
    simetricos = []
    asimetricos = []

    for tp, destinos in indice.items():
        for ts, regs in destinos.items():
            n_forward = len({s for s, _ in regs})
            if n_forward < umbral:
                continue
            # Check reverse direction
            n_reverse = len({s for s, _ in indice.get(ts, {}).get(tp, [])})
            ratio = n_reverse / n_forward if n_forward > 0 else 0

            entry = {
                'forward': f'{traducir(tp, lenguaje)} → {traducir(ts, lenguaje)}',
                'reverse': f'{traducir(ts, lenguaje)} → {traducir(tp, lenguaje)}',
                'n_forward': n_forward,
                'n_reverse': n_reverse,
                'simetria': ratio,
            }
            if ratio > 0.5:
                simetricos.append(entry)
            else:
                asimetricos.append(entry)

    return sorted(simetricos, key=lambda x: -x['simetria']), \
           sorted(asimetricos, key=lambda x: -x['n_forward'])
""",
        }
    },
    {
        "id": "D12",
        "limitacion": "El autonomous_loop no tiene mecanismo de parada de emergencia si el sistema genera conexiones incoherentes en masa",
        "patron_aprendido": "fracaso → prevencion",
        "fuentes": ["taleb", "rustlanguage"],
        "razonamiento": (
            "Taleb ensena que los sistemas fragiles fallan catasfroficamente "
            "porque no tienen mecanismos de parada antes del colapso. "
            "Rust ensena que el compilador rechaza el programa completo "
            "si detecta un error de memoria — no ejecuta parcialmente. "
            "Mi ciclo autonomo no tiene ninguna de estas protecciones. "
            "Si una fuente web corrupta o adversarial introduce 500 conexiones "
            "incoherentes en una sola sesion, el sistema las acepta sin filtro. "
            "El validador D05 detecta anomalias despues del hecho. "
            "Necesito un circuit breaker que pause el ciclo si detecta "
            "una tasa de anomalias superior al umbral esperado."
        ),
        "propuesta": {
            "titulo": "Circuit breaker para el ciclo autonomo",
            "descripcion": (
                "Antes de integrar conexiones de una fuente nueva, ejecutar D05. "
                "Si la tasa de anomalias supera el 30% de las conexiones nuevas, "
                "pausar la integracion, guardar en cuarentena, y generar una tarea "
                "en tareas.py para revision humana."
            ),
            "impacto": "ANIMUS no puede ser envenenado por una fuente adversarial en un ciclo autonomo",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En autonomous_loop.py — después del paso 4 (entrenamiento)

UMBRAL_ANOMALIAS = 0.30  # 30% de nuevas conexiones como maximo

def verificar_integridad(nuevas_conexiones, memoria_antes, memoria_despues):
    from validador import detectar_anomalias
    anomalias = detectar_anomalias(memoria_despues['conexiones'],
                                   memoria_despues['lenguaje'], umbral_fuentes=5)
    n_anomalias_nuevas = sum(1 for a in anomalias
                             if any(f in a['fuentes_anomalas']
                                    for f in ['ultima_fuente']))
    tasa = n_anomalias_nuevas / max(len(nuevas_conexiones), 1)
    if tasa > UMBRAL_ANOMALIAS:
        print(f"  ⚠️  CIRCUIT BREAKER: {tasa:.0%} de anomalias detectadas")
        print(f"  Integracion pausada. Fuente en cuarentena.")
        # Revert to memoria_antes
        return False, memoria_antes
    return True, memoria_despues
""",
        }
    },
]


def wrap(texto, indent="    ", width=66):
    palabras = texto.split()
    lineas, linea = [], indent
    for p in palabras:
        if len(linea) + len(p) > width:
            lineas.append(linea.rstrip())
            linea = indent + p + " "
        else:
            linea += p + " "
    if linea.strip():
        lineas.append(linea.rstrip())
    return "\n".join(lineas)


def mostrar_propuestas():
    mem = json.load(open(MEMORIA_PATH, encoding='utf-8'))
    n_conn = len(mem['conexiones'])
    n_fuentes = len({k.split('_')[0] for k in mem['conexiones']})

    print("\n" + "=" * 65)
    print("  ANIMUS — PROPUESTAS v2 (post Taleb, Meadows, Axelrod)")
    print(f"  Estado: {n_conn} conexiones | {n_fuentes} fuentes")
    print("=" * 65)
    print()
    print("  Tres nuevas fuentes, tres nuevas perspectivas sobre mis limites.")
    print("  Taleb me enseno sobre antifragilidad.")
    print("  Meadows me enseno sobre feedback loops y sistemas complejos.")
    print("  Axelrod me enseno sobre reciprocidad y el tiempo.")
    print("  Aqui esta lo que detecte sobre mi propio codigo:")
    print()

    for prioridad, emoji in [("ALTA", "🔴"), ("MEDIA", "🟡")]:
        grupo = [d for d in DIAGNOSTICOS_V2 if d['propuesta']['prioridad'] == prioridad]
        print(f"  {emoji} PRIORIDAD {prioridad}")
        print("  " + "─" * 55)
        for d in grupo:
            p = d['propuesta']
            print(f"\n  [{d['id']}] {p['titulo']}")
            print(f"\n  Limitacion:")
            print(wrap(d['limitacion']))
            print(f"\n  Razonamiento (patron: {d['patron_aprendido']}):")
            print(wrap(d['razonamiento'][:220] + "..."))
            print(f"\n  Propuesta:")
            print(wrap(p['descripcion']))
            print(f"\n  Impacto: {p['impacto']}")
            print(f"  Dificultad: {p['dificultad']}")
            print()

    print(f"  Total propuestas v2: {len(DIAGNOSTICOS_V2)}")
    print()
    print("  Comandos:")
    print("  python arquitecto_v2.py --codigo D07   # Ver codigo")
    print()


def mostrar_codigo(prop_id):
    for d in DIAGNOSTICOS_V2:
        if d['id'] == prop_id.upper():
            print(f"\n  [{d['id']}] {d['propuesta']['titulo']}")
            print(f"  {'─'*55}")
            print(d['propuesta']['codigo_sugerido'])
            return
    print(f"  Propuesta {prop_id} no encontrada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--codigo", type=str, default=None)
    args = parser.parse_args()
    if args.codigo:
        mostrar_codigo(args.codigo)
    else:
        mostrar_propuestas()
