# -*- coding: utf-8 -*-
"""D14 — Detector de Fuentes Primarias vs Curadas"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

FUENTES_CURADAS = {
    'biblia','tao','arte','meditaciones','kuhn','polya','dawkins','plato',
    'tanenbaum','networks','clanguage','pragmaticprog','unixhistory','kleppmann',
    'rustlanguage','godel','code','taleb','meadows','axelrod','meadows_loops',
    'meadows_loops2','diamond','shirer','acemoglu','graeber','klein','klein2',
    'mitchell','libro','how','Fukuyama','master','nueva',
    'animus_self_v3','animus_self_v4','animus_self_v5',
    'animus_self_v6','animus_self_v7','animus_self_v8',
}

FUENTES_PRIMARIAS = {
    'sciencedaily.com','techcrunch.com','bbc.com','weforum.org','hbr.org',
    'store.hbr.org','expansion.com','eleconomista.es','elpais.com','mckinsey.com',
    'spectrum.ieee.org','plato.stanford.edu','arxiv.org',
    'sciencedaily','weforum','techcrunch','bbc','hbr','mckinsey',
    'spectrum','expansion','eleconomista','elpais',
}

def clasificar_fuente(nombre):
    if nombre in FUENTES_CURADAS:
        return 'curada'
    if nombre in FUENTES_PRIMARIAS:
        return 'primaria'
    if '.' in nombre:
        return 'primaria'
    return 'curada'

def detectar_loops(indice):
    loops_b, loops_r, vistos_b, vistos_r = [], [], set(), set()
    for a, destinos in indice.items():
        for b in destinos:
            if a in indice.get(b, set()):
                pair = tuple(sorted([a, b]))
                if pair not in vistos_b:
                    vistos_b.add(pair)
                    loops_b.append([a, b])
    for a in indice:
        for b in indice[a]:
            for c in indice.get(b, set()):
                if a in indice.get(c, set()) and c != a and b != a:
                    key = tuple(sorted([a, b, c]))
                    if key not in vistos_r:
                        vistos_r.add(key)
                        loops_r.append([a, b, c])
    return loops_b, loops_r

def analizar_subgrafos(memoria):
    conexiones = memoria['conexiones']
    lenguaje   = memoria['lenguaje']

    def traducir(token):
        c = [(k.split('__=')[0], v) for k, v in lenguaje.items() if k.endswith(f'__={token}')]
        return max(c, key=lambda x: x[1])[0] if c else token

    conn_c, conn_p, clases = {}, {}, {}
    for k, v in conexiones.items():
        src = k.split('_')[0]
        t = clasificar_fuente(src)
        clases[src] = t
        (conn_c if t == 'curada' else conn_p)[k] = v

    def build_idx(conns):
        idx = defaultdict(set)
        for k in conns:
            p = k.split('__>')
            if len(p) == 2:
                idx[p[0].split('_')[-1]].add(p[1].split('_')[-1])
        return idx

    lb_c, lr_c = detectar_loops(build_idx(conn_c))
    lb_p, lr_p = detectar_loops(build_idx(conn_p))

    n_c = len({k.split('_')[0] for k in conn_c})
    n_p = len({k.split('_')[0] for k in conn_p})

    print(f"\n{'='*65}")
    print(f"  D14 — SUBGRAFOS: CURADO vs PRIMARIO")
    print(f"{'='*65}")
    print(f"\n  CURADO  ({n_c} fuentes, {len(conn_c)} conexiones)")
    print(f"    Loops: balance={len(lb_c)}  refuerzo={len(lr_c)}  → {'DAG ✓' if not lb_c and not lr_c else '⚡ LOOPS'}")
    print(f"\n  PRIMARIO ({n_p} fuentes, {len(conn_p)} conexiones)")
    print(f"    Loops: balance={len(lb_p)}  refuerzo={len(lr_p)}  → {'DAG ✓' if not lb_p and not lr_p else '⚡ LOOPS DETECTADOS'}")

    if lb_p or lr_p:
        print(f"\n  ⚡ HIPÓTESIS DAG FALSIFICADA en fuentes primarias:")
        for l in (lb_p + lr_p)[:5]:
            print(f"    {' → '.join(traducir(t) for t in l)} → {traducir(l[0])}")

    print(f"\n  Fuentes primarias ({n_p}):")
    for src, t in sorted(clases.items()):
        if t == 'primaria':
            print(f"    📊 {src}")

    resultado = {
        'fecha': datetime.now().isoformat(),
        'curado': {'fuentes': n_c, 'conexiones': len(conn_c),
                   'loops': len(lb_c)+len(lr_c), 'es_dag': not lb_c and not lr_c},
        'primario': {'fuentes': n_p, 'conexiones': len(conn_p),
                     'loops': len(lb_p)+len(lr_p), 'es_dag': not lb_p and not lr_p},
        'hipotesis_dag_sostenida': not lb_p and not lr_p,
    }
    Path('d14_subgrafos.json').write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  Guardado: d14_subgrafos.json")
    return resultado

if __name__ == "__main__":
    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)
    analizar_subgrafos(mem)
