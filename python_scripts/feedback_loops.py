# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo Feedback Loops (D08)
Detecta loops de retroalimentacion en el grafo de conocimiento.
Inspirado en Meadows (Thinking in Systems) y Axelrod (Evolution of Cooperation).

Uso:
    python feedback_loops.py            # Detectar todos los loops
    python feedback_loops.py --min 3    # Solo loops con 3+ fuentes por arco
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

TOKEN_ES = {
    "failure":"fracaso","gap":"brecha","crisis":"crisis","collapse":"colapso",
    "limitation":"limitacion","algorithm":"algoritmo","regulation":"regulacion",
    "cooperation":"cooperacion","developed":"desarrollo","discovered":"descubrimiento",
    "framework":"arquitectura","prevention":"prevencion","reform":"reforma",
    "education":"aprendizaje","innovation":"innovacion","neural":"neuronal",
}

def traducir(token, lenguaje=None):
    if lenguaje:
        candidatos = [(k.split('__=')[0], v) for k, v in lenguaje.items()
                      if k.endswith(f'__={token}')]
        if candidatos:
            return max(candidatos, key=lambda x: x[1])[0]
    return TOKEN_ES.get(token, token)


def construir_grafo(conexiones, min_fuentes=3):
    """Build adjacency graph filtering by minimum source count."""
    conteo = defaultdict(lambda: defaultdict(set))
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2: continue
        tp = p[0].split('_')[-1]
        ts = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        conteo[tp][ts].add(src)

    grafo = defaultdict(set)
    fuentes_arco = {}
    for tp, destinos in conteo.items():
        for ts, srcs in destinos.items():
            if len(srcs) >= min_fuentes:
                grafo[tp].add(ts)
                fuentes_arco[(tp, ts)] = srcs
    return grafo, fuentes_arco


def detectar_loops_balance(grafo, fuentes_arco, lenguaje):
    """Loops of 2: A→B and B→A — stabilizing feedback."""
    loops = []
    vistos = set()
    for a in grafo:
        for b in grafo[a]:
            if a in grafo.get(b, set()):
                key = tuple(sorted([a, b]))
                if key not in vistos:
                    vistos.add(key)
                    srcs_ab = fuentes_arco.get((a, b), set())
                    srcs_ba = fuentes_arco.get((b, a), set())
                    loops.append({
                        'tipo': 'BALANCE',
                        'arcos': [f"{traducir(a, lenguaje)} → {traducir(b, lenguaje)}",
                                  f"{traducir(b, lenguaje)} → {traducir(a, lenguaje)}"],
                        'tokens': [a, b],
                        'fuentes_ab': len(srcs_ab),
                        'fuentes_ba': len(srcs_ba),
                        'interpretacion': (
                            f"Cuando {traducir(a, lenguaje)} ocurre, genera {traducir(b, lenguaje)}. "
                            f"Pero {traducir(b, lenguaje)} a su vez genera mas {traducir(a, lenguaje)}. "
                            f"Este loop puede ser estabilizador o amplificador segun el contexto."
                        )
                    })
    return loops


def detectar_loops_refuerzo(grafo, fuentes_arco, lenguaje):
    """Loops of 3: A→B→C→A — reinforcing feedback."""
    loops = []
    vistos = set()
    tokens = list(grafo.keys())
    for a in tokens:
        for b in grafo[a]:
            for c in grafo.get(b, set()):
                if a in grafo.get(c, set()) and c != a and b != a:
                    key = tuple(sorted([a, b, c]))
                    if key not in vistos:
                        vistos.add(key)
                        loops.append({
                            'tipo': 'REFUERZO',
                            'arcos': [
                                f"{traducir(a, lenguaje)} → {traducir(b, lenguaje)}",
                                f"{traducir(b, lenguaje)} → {traducir(c, lenguaje)}",
                                f"{traducir(c, lenguaje)} → {traducir(a, lenguaje)}",
                            ],
                            'tokens': [a, b, c],
                            'fuentes': [
                                len(fuentes_arco.get((a,b), set())),
                                len(fuentes_arco.get((b,c), set())),
                                len(fuentes_arco.get((c,a), set())),
                            ],
                            'interpretacion': (
                                f"Loop de refuerzo: {traducir(a, lenguaje)} → "
                                f"{traducir(b, lenguaje)} → {traducir(c, lenguaje)} → "
                                f"{traducir(a, lenguaje)}. "
                                f"Segun Meadows, este tipo de loop puede amplificarse "
                                f"hasta que una restriccion externa lo limite."
                            )
                        })
    return loops


def mostrar_reporte(loops_balance, loops_refuerzo):
    print("\n" + "=" * 65)
    print("  ANIMUS — DETECTOR DE FEEDBACK LOOPS (D08)")
    print("  Inspirado en Meadows: todo sistema complejo tiene loops")
    print("=" * 65)

    if not loops_balance and not loops_refuerzo:
        print("\n  ✅ No se detectaron loops de retroalimentacion.")
        print("  El grafo actual es un DAG (directed acyclic graph).")
        print("  Todos los patrones son causalidades lineales.")
        print()
        print("  Interpretacion (Meadows):")
        print("  Un grafo sin loops es predecible pero fragil.")
        print("  Los sistemas reales tienen loops que los hacen")
        print("  adaptativos. Esto sugiere que el conocimiento de")
        print("  ANIMUS aun no captura las dinamicas de retroalimentacion")
        print("  que existen en los sistemas que estudia.")
        print()
        print("  Accion recomendada: incorporar fuentes que documenten")
        print("  explicitamente los ciclos de retroalimentacion —")
        print("  Meadows tiene ejemplos concretos en capitulos 2-4.")
        return

    if loops_balance:
        print(f"\n  🔄 LOOPS DE BALANCE (A↔B): {len(loops_balance)}")
        print("  " + "─" * 55)
        for loop in loops_balance[:5]:
            print(f"\n  {' ↔ '.join(loop['arcos'])}")
            print(f"  Fuentes: {loop['fuentes_ab']} / {loop['fuentes_ba']}")
            print(f"  {loop['interpretacion']}")

    if loops_refuerzo:
        print(f"\n  🌀 LOOPS DE REFUERZO (A→B→C→A): {len(loops_refuerzo)}")
        print("  " + "─" * 55)
        for loop in loops_refuerzo[:5]:
            min_f = min(loop['fuentes'])
            print(f"\n  {' → '.join(loop['arcos'][:3])}")
            print(f"  Fuentes minimas en el ciclo: {min_f}")
            print(f"  {loop['interpretacion']}")

    print(f"\n  Total loops detectados: {len(loops_balance) + len(loops_refuerzo)}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=3,
                        help="Fuentes minimas por arco (default: 3)")
    args = parser.parse_args()

    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)

    grafo, fuentes_arco = construir_grafo(mem['conexiones'], args.min)
    lenguaje = mem['lenguaje']

    loops_balance = detectar_loops_balance(grafo, fuentes_arco, lenguaje)
    loops_refuerzo = detectar_loops_refuerzo(grafo, fuentes_arco, lenguaje)

    mostrar_reporte(loops_balance, loops_refuerzo)
