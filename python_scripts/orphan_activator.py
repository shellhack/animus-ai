# -*- coding: utf-8 -*-
"""
D17 — Activador de Tokens Huérfanos
Identifica tokens que solo aparecen como destino (nunca como origen)
y genera búsquedas dirigidas para encontrar fuentes que los documenten
como ORIGEN — potencialmente creando el primer loop del grafo.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

TOKEN_ES = {
    "algorithm":"algoritmo","automation":"automatización","cooperation":"cooperación",
    "developed":"desarrollo","discovered":"descubrimiento","transformed":"transformación",
    "regulation":"regulación","education":"educación","innovation":"innovación",
    "reform":"reforma","prevention":"prevención","framework":"arquitectura",
    "neural":"neuronal","training":"entrenamiento","cooperation":"cooperación",
    "blockchain":"blockchain","crispr":"crispr","coalition":"coalición",
    "community":"comunidad","awareness":"conciencia","breakthrough":"avance",
    "battery":"batería","artificial":"inteligencia artificial",
}

# Queries to find sources that document tokens as ORIGINS (not just destinations)
QUERIES_HUERFANOS = {
    "algorithm": [
        "when algorithms fail consequences",
        "algorithmic systems creating new problems",
        "unintended consequences of automation algorithms",
    ],
    "automation": [
        "automation creates unemployment new problems",
        "automation failure risks",
        "side effects of industrial automation",
    ],
    "cooperation": [
        "when cooperation breaks down failure",
        "cooperation collapse tragedy of the commons",
        "limits of international cooperation",
    ],
    "regulation": [
        "regulatory capture creates new failures",
        "when regulation causes more problems",
        "unintended consequences of regulation",
    ],
    "innovation": [
        "innovation creates inequality disruption",
        "creative destruction negative effects",
        "innovation side effects problems",
    ],
    "reform": [
        "reform failure backlash consequences",
        "when reforms make things worse",
        "reform unintended consequences history",
    ],
}

def analizar_huerfanos(memoria):
    conexiones = memoria['conexiones']
    lenguaje   = memoria['lenguaje']

    orig = set()
    dest = set()
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2:
            orig.add(p[0].split('_')[-1])
            dest.add(p[1].split('_')[-1])

    huerfanos = sorted(dest - orig)

    # Count how many patterns end at each orphan
    peso_huerfano = defaultdict(float)
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) == 2:
            ts = p[1].split('_')[-1]
            if ts in (dest - orig):
                peso_huerfano[ts] += v

    huerfanos_ordenados = sorted(huerfanos, key=lambda x: -peso_huerfano[x])

    print(f"\n{'='*65}")
    print(f"  D17 — ACTIVADOR DE TOKENS HUÉRFANOS")
    print(f"{'='*65}")
    print(f"\n  Tokens solo-destino: {len(huerfanos)}")
    print(f"  (Aparecen como resolución pero nunca como problema)")
    print(f"\n  TOP 10 por peso acumulado:")
    for t in huerfanos_ordenados[:10]:
        nombre = TOKEN_ES.get(t, t)
        bar = '█' * min(int(peso_huerfano[t] / 200), 12)
        print(f"    {nombre:25} peso:{peso_huerfano[t]:6.0f}  {bar}")

    print(f"\n  POTENCIAL PARA LOOPS:")
    print(f"  Si alguno de estos tokens aparece como ORIGEN en una fuente nueva,")
    print(f"  se crea el primer camino hacia un loop en el grafo.")
    print(f"\n  Ejemplo de loop potencial:")
    top = huerfanos_ordenados[0]
    # Find what generates the top orphan
    generadores = set()
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2 and p[1].split('_')[-1] == top:
            generadores.add(p[0].split('_')[-1])
    if generadores:
        gen = list(generadores)[0]
        print(f"    {gen} → {top} → {gen}  ← este loop requiere que '{top}' genere '{gen}'")

    print(f"\n  QUERIES PARA ACTIVAR TOKENS HUÉRFANOS:")
    for token in huerfanos_ordenados[:5]:
        nombre = TOKEN_ES.get(token, token)
        queries = QUERIES_HUERFANOS.get(token, [
            f"when {token} creates new problems",
            f"{token} failure consequences",
            f"limits of {token}",
        ])
        print(f"\n  🎯 {nombre.upper()} (peso: {peso_huerfano[token]:.0f})")
        for q in queries[:2]:
            print(f"     🔍 {q}")

    resultado = {
        'fecha': datetime.now().isoformat(),
        'total_huerfanos': len(huerfanos),
        'huerfanos_por_peso': [
            {'token': t, 'nombre': TOKEN_ES.get(t, t), 'peso': peso_huerfano[t]}
            for t in huerfanos_ordenados[:15]
        ],
        'loop_potencial': f"{list(generadores)[0] if generadores else '?'} → {top} → {list(generadores)[0] if generadores else '?'}",
    }

    Path('d17_huerfanos.json').write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  Guardado: d17_huerfanos.json")
    return resultado

if __name__ == "__main__":
    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)
    analizar_huerfanos(mem)
