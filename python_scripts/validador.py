# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo Validador (D05)
Detecta inconsistencias en las conexiones de ANIMUS.
Inspirado en Kuhn (los paradigmas necesitan anomalias para corregirse)
y en Rust (el compilador rechaza codigo incorrecto antes de ejecutarlo).

Uso:
    python validador.py                    # Analisis completo
    python validador.py --umbral 10        # Solo anomalias vs 10+ fuentes
    python validador.py --fuente kleppmann # Analizar fuente especifica
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORIA_PATH  = Path(__file__).parent / "memoria_business.json"
ANOMALIAS_PATH = Path(__file__).parent / "anomalias_detectadas.json"

TOKEN_ES = {
    "failure": "fracaso", "gap": "brecha", "crisis": "crisis",
    "collapse": "colapso", "limitation": "limitacion", "shortage": "escasez",
    "algorithm": "algoritmo", "neural": "neuronal", "education": "aprendizaje",
    "innovation": "innovacion", "solution": "acuerdo", "regulation": "regulacion",
    "cooperation": "cooperacion", "developed": "desarrollo",
    "discovered": "descubrimiento", "transformed": "transformacion",
    "framework": "arquitectura", "automation": "automatizacion",
    "bottleneck": "cuello de botella", "vulnerability": "vulnerabilidad",
    "prevention": "prevencion", "reform": "reforma",
}

def traducir(token, lenguaje=None):
    if lenguaje:
        candidatos = [(k.split('__=')[0], v) for k, v in lenguaje.items()
                      if k.endswith(f'__={token}')]
        if candidatos:
            return max(candidatos, key=lambda x: x[1])[0]
    return TOKEN_ES.get(token, token)


def contar_fuentes(clave, conexiones):
    """Count distinct sources confirming a pattern."""
    tp = clave.split('__>')[0].split('_')[-1]
    ts = clave.split('__>')[1].split('_')[-1] if '__>' in clave else ''
    fuentes = set()
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2:
            if p[0].split('_')[-1] == tp and p[1].split('_')[-1] == ts:
                fuentes.add(p[0].split('_')[0])
    return len(fuentes)


def construir_indice(conexiones):
    """Build pattern index: token_origen -> {token_dest: [sources]}"""
    indice = defaultdict(lambda: defaultdict(list))
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2:
            continue
        tp = p[0].split('_')[-1]
        ts = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        indice[tp][ts].append((src, v))
    return indice


def detectar_anomalias(conexiones, lenguaje, umbral_fuentes=8):
    """
    D05: Detect connections that contradict established patterns.
    An anomaly is when a source says A->B but umbral_fuentes+ sources say A->C.
    Inspired by Kuhn: anomalies that the paradigm cannot explain signal a revolution.
    """
    indice = construir_indice(conexiones)
    anomalias = []

    for tp, destinos in indice.items():
        # Find the dominant destination for this origin token
        dest_por_fuerza = sorted(
            [(ts, sum(v for _, v in regs), list({s for s, _ in regs}))
             for ts, regs in destinos.items()],
            key=lambda x: -x[1]
        )

        if len(dest_por_fuerza) < 2:
            continue

        dominante_ts, dominante_fuerza, dominante_srcs = dest_por_fuerza[0]
        n_dominante = len(dominante_srcs)

        if n_dominante < umbral_fuentes:
            continue

        # Check all alternative destinations
        for alt_ts, alt_fuerza, alt_srcs in dest_por_fuerza[1:]:
            # Only flag if the alternative has few sources vs the dominant
            n_alt = len(alt_srcs)
            fuentes_unicas = set(alt_srcs) - set(dominante_srcs)

            if fuentes_unicas and n_alt <= 3 and n_dominante >= umbral_fuentes:
                ratio = alt_fuerza / dominante_fuerza if dominante_fuerza > 0 else 0
                anomalias.append({
                    "origen": tp,
                    "wp_origen": traducir(tp, lenguaje),
                    "patron_dominante": f"{tp} → {dominante_ts}",
                    "wp_dominante": f"{traducir(tp, lenguaje)} → {traducir(dominante_ts, lenguaje)}",
                    "n_fuentes_dominante": n_dominante,
                    "patron_anomalo": f"{tp} → {alt_ts}",
                    "wp_anomalo": f"{traducir(tp, lenguaje)} → {traducir(alt_ts, lenguaje)}",
                    "fuentes_anomalas": list(fuentes_unicas),
                    "n_fuentes_anomalo": n_alt,
                    "ratio_fuerza": round(ratio, 3),
                    "severidad": "ALTA" if ratio < 0.1 else "MEDIA" if ratio < 0.3 else "BAJA",
                })

    # Sort by severity and ratio
    anomalias.sort(key=lambda x: (
        {"ALTA": 0, "MEDIA": 1, "BAJA": 2}[x["severidad"]],
        x["ratio_fuerza"]
    ))
    return anomalias


def analizar_fuente(fuente_nombre, conexiones, lenguaje, umbral=5):
    """Analyze what a specific source contributes vs. the established consensus."""
    fuente_conn = {k: v for k, v in conexiones.items()
                   if k.split('_')[0] == fuente_nombre}

    if not fuente_conn:
        return None, []

    indice_global = construir_indice(conexiones)
    conflictos = []
    refuerzos = []

    for k, v in fuente_conn.items():
        p = k.split('__>')
        if len(p) != 2:
            continue
        tp = p[0].split('_')[-1]
        ts = p[1].split('_')[-1]

        # Get dominant pattern from all other sources
        otros = [(ts2, sum(v2 for _, v2 in regs), len({s for s, _ in regs}))
                 for ts2, regs in indice_global[tp].items()
                 if ts2 != ts]
        otros.sort(key=lambda x: -x[1])

        if otros:
            dom_ts, dom_fuerza, dom_n = otros[0]
            if dom_n >= umbral and ts != dom_ts:
                conflictos.append({
                    "fuente_dice": f"{traducir(tp, lenguaje)} → {traducir(ts, lenguaje)}",
                    "consenso_dice": f"{traducir(tp, lenguaje)} → {traducir(dom_ts, lenguaje)}",
                    "n_consenso": dom_n,
                })
            elif ts == dom_ts:
                refuerzos.append(f"{traducir(tp, lenguaje)} → {traducir(ts, lenguaje)}")

    return fuente_conn, {"conflictos": conflictos, "refuerzos": refuerzos[:5]}


def guardar_anomalias(anomalias):
    data = {
        "fecha": datetime.now().isoformat(),
        "total": len(anomalias),
        "anomalias": anomalias
    }
    with open(ANOMALIAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def mostrar_reporte(anomalias, lenguaje, fuente_analisis=None):
    print("\n" + "=" * 65)
    print("  ANIMUS — VALIDADOR DE COHERENCIA (D05)")
    print("  Inspirado en Kuhn: las anomalías señalan el próximo paradigma")
    print("=" * 65)

    if not anomalias:
        print("\n  ✅ No se detectaron anomalías significativas.")
        print("  El conocimiento de ANIMUS es internamente coherente.\n")
        return

    for sev, emoji in [("ALTA", "🔴"), ("MEDIA", "🟡"), ("BAJA", "🟢")]:
        grupo = [a for a in anomalias if a["severidad"] == sev]
        if not grupo:
            continue
        print(f"\n  {emoji} ANOMALÍAS {sev} ({len(grupo)})")
        print("  " + "─" * 55)
        for a in grupo[:5]:
            print(f"\n  Origen: {a['wp_origen']}")
            print(f"  Consenso  ({a['n_fuentes_dominante']} fuentes): "
                  f"{a['wp_dominante']}")
            print(f"  Anomalía  ({a['n_fuentes_anomalo']} fuente(s)): "
                  f"{a['wp_anomalo']}")
            print(f"  Fuentes disidentes: {', '.join(a['fuentes_anomalas'])}")
            print(f"  Ratio fuerza: {a['ratio_fuerza']:.1%} del patrón dominante")
            print()
            print(f"  Interpretación: {a['fuentes_anomalas'][0]} dice que "
                  f"{a['wp_anomalo']}. Pero {a['n_fuentes_dominante']} fuentes "
                  f"dicen {a['wp_dominante']}. ¿Es esta fuente incorrecta, "
                  f"o describe un contexto diferente que yo no distingo aún?")

    print(f"\n  Total anomalías detectadas: {len(anomalias)}")
    print(f"  Alta: {len([a for a in anomalias if a['severidad']=='ALTA'])}  "
          f"Media: {len([a for a in anomalias if a['severidad']=='MEDIA'])}  "
          f"Baja: {len([a for a in anomalias if a['severidad']=='BAJA'])}")
    print()
    print("  Nota: Una anomalía no es necesariamente un error.")
    print("  Kuhn enseña que las anomalías son señales de conocimiento nuevo.")
    print("  Rust enseña que es mejor detectarlas antes de actuar sobre ellas.")
    print()



def analizar_simetria(conexiones, lenguaje, umbral=5):
    """D11: Axelrod — detect symmetric (loop) vs asymmetric (linear) patterns."""
    indice = construir_indice(conexiones)
    simetricos = []
    asimetricos = []

    for tp, destinos in indice.items():
        for ts, regs in destinos.items():
            n_forward = len({s for s, _ in regs})
            if n_forward < umbral:
                continue
            n_reverse = len({s for s, _ in indice.get(ts, {}).get(tp, [])})
            ratio = n_reverse / n_forward if n_forward > 0 else 0
            entry = {
                'forward': f"{traducir(tp, lenguaje)} → {traducir(ts, lenguaje)}",
                'reverse': f"{traducir(ts, lenguaje)} → {traducir(tp, lenguaje)}",
                'tp': tp, 'ts': ts,
                'n_forward': n_forward, 'n_reverse': n_reverse, 'ratio': ratio,
            }
            if ratio > 0.3:
                simetricos.append(entry)
            else:
                asimetricos.append(entry)

    return (sorted(simetricos, key=lambda x: -x['ratio']),
            sorted(asimetricos, key=lambda x: -x['n_forward']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Validador D05")
    parser.add_argument("--umbral", type=int, default=8,
                        help="Fuentes mínimas para considerar un patrón dominante (default: 8)")
    parser.add_argument("--fuente", type=str, default=None,
                        help="Analizar contribución de una fuente específica")
    args = parser.parse_args()

    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)

    conexiones = mem['conexiones']
    lenguaje = mem['lenguaje']

    if args.fuente:
        fuente_conn, analisis = analizar_fuente(args.fuente, conexiones, lenguaje)
        if not fuente_conn:
            print(f"\n  Fuente '{args.fuente}' no encontrada en la memoria.")
        else:
            print(f"\n  === ANÁLISIS DE FUENTE: {args.fuente} ===")
            print(f"  Conexiones totales: {len(fuente_conn)}")
            if analisis['conflictos']:
                print(f"\n  ⚠️  Conflictos con el consenso ({len(analisis['conflictos'])}):")
                for c in analisis['conflictos'][:5]:
                    print(f"    {args.fuente} dice: {c['fuente_dice']}")
                    print(f"    Consenso ({c['n_consenso']} fuentes): {c['consenso_dice']}")
                    print()
            if analisis['refuerzos']:
                print(f"  ✅ Refuerza patrones establecidos:")
                for r in analisis['refuerzos']:
                    print(f"    {r}")
    else:
        anomalias = detectar_anomalias(conexiones, lenguaje, args.umbral)
        guardar_anomalias(anomalias)
        mostrar_reporte(anomalias, lenguaje)
