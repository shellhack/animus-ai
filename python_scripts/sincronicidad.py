# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo Sincronicidad
Convierte el aprendizaje de pasivo a activo y dirigido.

Flujo:
  1. validador.py detecta anomalías y patrones débiles
  2. sincronicidad.py analiza qué falta
  3. genera queries de búsqueda específicas
  4. encola fuentes prioritarias para el ciclo autónomo

Uso:
    python sincronicidad.py              # Análisis completo
    python sincronicidad.py --ejecutar   # Ejecutar búsquedas web
    python sincronicidad.py --cola       # Ver cola de fuentes pendientes
"""

import json
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORIA_PATH  = Path(__file__).parent / "memoria_business.json"
COLA_PATH     = Path(__file__).parent / "cola_sincronicidad.json"
TAREAS_PATH   = Path(__file__).parent / "tareas_pendientes.json"

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


# ── Análisis de brechas ───────────────────────────────────────────────────────

def detectar_brechas(memoria):
    """Find knowledge gaps: strong patterns with few sources."""
    conexiones = memoria['conexiones']
    lenguaje   = memoria['lenguaje']

    conteo = defaultdict(lambda: defaultdict(list))
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2: continue
        tp  = p[0].split('_')[-1]
        ts  = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        conteo[tp][ts].append((src, v))

    brechas = []
    for tp, destinos in conteo.items():
        for ts, regs in destinos.items():
            n_src  = len({s for s, _ in regs})
            fuerza = sum(v for _, v in regs)
            if 1 <= n_src <= 4 and fuerza > 30:
                brechas.append({
                    'tp': tp, 'ts': ts,
                    'wp': traducir(tp, lenguaje),
                    'ws': traducir(ts, lenguaje),
                    'n_src': n_src,
                    'fuerza': fuerza,
                    'fuentes': list({s for s, _ in regs}),
                })

    brechas.sort(key=lambda x: (-x['fuerza'], x['n_src']))
    return brechas


def detectar_puntos_ciegos(memoria):
    """Find tokens that only appear as destinations — never as origins.
    These are resolution tokens with no known antecedents beyond what we have.
    Also find strong asymmetries: A→B strong but B→A zero.
    """
    conexiones = memoria['conexiones']
    lenguaje   = memoria['lenguaje']

    orig_tokens = set()
    dest_tokens = set()
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2:
            orig_tokens.add(p[0].split('_')[-1])
            dest_tokens.add(p[1].split('_')[-1])

    solo_destino = dest_tokens - orig_tokens
    return [{'token': t, 'nombre': traducir(t, lenguaje)} for t in sorted(solo_destino)]


def detectar_anomalias_activas(memoria, umbral=5):
    """Find sources that contradict the consensus — Kuhn anomalies."""
    conexiones = memoria['conexiones']
    lenguaje   = memoria['lenguaje']

    consensus = defaultdict(lambda: defaultdict(list))
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2: continue
        tp  = p[0].split('_')[-1]
        ts  = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        consensus[tp][ts].append((src, v))

    anomalias = []
    for tp, destinos in consensus.items():
        srcs_tp = set()
        for ts, regs in destinos.items():
            srcs_tp.update(s for s, _ in regs)

        for ts, regs in destinos.items():
            n_confirm = len({s for s, _ in regs})
            if n_confirm < umbral:
                continue
            srcs_confirm = {s for s, _ in regs}
            srcs_contradict = srcs_tp - srcs_confirm
            if len(srcs_contradict) >= 2:
                anomalias.append({
                    'tp': tp, 'ts': ts,
                    'wp': traducir(tp, lenguaje),
                    'ws': traducir(ts, lenguaje),
                    'n_confirm': n_confirm,
                    'n_contradict': len(srcs_contradict),
                    'fuentes_confirman': list(srcs_confirm)[:3],
                    'fuentes_contradicen': list(srcs_contradict)[:3],
                })

    anomalias.sort(key=lambda x: -x['n_contradict'])
    return anomalias


# ── Generación de queries ─────────────────────────────────────────────────────

def generar_queries(brechas, puntos_ciegos, anomalias):
    """Generate targeted search queries for each gap type."""
    queries = []

    # Queries for weak patterns (1-4 sources, high strength)
    for b in brechas[:6]:
        wp, ws = b['wp'], b['ws']
        # Map to English for better web search results
        EN_MAP = {
            'fracaso':'failure','colapso':'collapse','crisis':'crisis',
            'brecha':'gap','corrupción':'corruption','fraude':'fraud',
            'desigualdad':'inequality','regulación':'regulation',
            'algoritmo':'algorithm','reforma':'reform','desarrollo':'development',
            'educación':'education','cooperación':'cooperation','arquitectura':'architecture',
            'innovación':'innovation','política':'policy','transformación':'transformation',
        }
        wp_en = EN_MAP.get(wp, wp)
        ws_en = EN_MAP.get(ws, ws)
        q = {
            'tipo': 'brecha',
            'patron': f"{wp} → {ws}",
            'n_src': b['n_src'],
            'fuerza': b['fuerza'],
            'queries': [
                f"how {wp_en} leads to {ws_en} historical examples",
                f"{wp_en} causes {ws_en} institutional case study",
                f"{wp_en} {ws_en} relationship systems theory",
            ],
            'razon': f"Patrón fuerte ({b['fuerza']:.0f}) pero solo {b['n_src']} fuente(s). "
                     f"Necesita confirmación independiente."
        }
        queries.append(q)

    # Queries for the reform-emergent vs reform-imposed gap (Klein anomaly)
    queries.append({
        'tipo': 'vocabulario_nuevo',
        'patron': 'reforma emergente vs reforma impuesta',
        'queries': [
            "emergent reform vs imposed reform crisis capitalism",
            "shock doctrine critique institutional reform spontaneous",
            "crisis exploitation vs crisis response institutional economics",
        ],
        'razon': 'Klein intentó documentar reforma impuesta pero el vocabulario no la captura. '
                 'Se necesitan fuentes que distingan entre reforma que surge del fracaso '
                 'y reforma que explota el fracaso.'
    })

    # Queries for Fukuyama's failure vs collapse distinction
    queries.append({
        'tipo': 'vocabulario_nuevo',
        'patron': 'fracaso (evento) vs colapso (proceso)',
        'queries': [
            "systemic collapse vs failure distinction political theory",
            "state failure vs state collapse Rotberg",
            "gradual collapse vs acute failure resilience",
        ],
        'razon': 'Strange loop v7 identificó que fracaso≠colapso. '
                 'Rotberg y otros distinguen explícitamente state failure de state collapse.'
    })

    # Queries for anomalies — sources that contradict consensus
    EN_MAP = {
        'fracaso':'failure','colapso':'collapse','crisis':'crisis',
        'brecha':'gap','corrupción':'corruption','fraude':'fraud',
        'desigualdad':'inequality','regulación':'regulation',
        'algoritmo':'algorithm','reforma':'reform','desarrollo':'development',
        'educación':'education','cooperación':'cooperation','arquitectura':'architecture',
        'innovación':'innovation','política':'policy','transformación':'transformation',
    }
    for a in anomalias[:3]:
        queries.append({
            'tipo': 'anomalia',
            'patron': f"{a['wp']} → {a['ws']}",
            'n_confirm': a['n_confirm'],
            'n_contradict': a['n_contradict'],
            'queries': [
                f"does {EN_MAP.get(a["wp"], a["wp"])} always lead to {EN_MAP.get(a["ws"], a["ws"])} counterexamples",
                f"when {EN_MAP.get(a["wp"], a["wp"])} does not produce {EN_MAP.get(a["ws"], a["ws"])} exceptions",
                f"{EN_MAP.get(a["wp"], a["wp"])} without {EN_MAP.get(a["ws"], a["ws"])} historical cases",
            ],
            'razon': f"Patrón confirmado por {a['n_confirm']} fuentes pero "
                     f"contradicho por {a['n_contradict']}. Kuhn: las anomalías son información."
        })

    return queries


# ── Búsqueda web ──────────────────────────────────────────────────────────────

def buscar_url(query, max_results=3):
    """Search DuckDuckGo for URLs relevant to a query."""
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ANIMUS/1.0)'
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')

        import re
        links = re.findall(r'href="(https?://[^"&]{15,})"', html)
        # Filter out ads and DDG internal links
        filtered = [l for l in links
                    if not any(x in l for x in
                               ['duckduckgo','google','bing','facebook',
                                'twitter','amazon','youtube'])]
        return list(dict.fromkeys(filtered))[:max_results]
    except Exception as e:
        return []


def ejecutar_busquedas(queries):
    """Execute web searches and collect URLs for each gap."""
    print("\n  Ejecutando búsquedas dirigidas...\n")
    resultados = []

    for q in queries:
        print(f"  [{q['tipo'].upper()}] {q['patron']}")
        urls_encontradas = []
        for query_str in q['queries'][:2]:  # max 2 queries per gap
            urls = buscar_url(query_str)
            urls_encontradas.extend(urls)
            if urls:
                print(f"    ✓ '{query_str[:50]}...' → {len(urls)} URLs")
            else:
                print(f"    ✗ '{query_str[:50]}...' → sin resultados")

        resultados.append({
            **q,
            'urls': list(dict.fromkeys(urls_encontradas))[:5],
            'timestamp': datetime.now().isoformat()
        })

    return resultados


# ── Cola de fuentes ───────────────────────────────────────────────────────────

def actualizar_cola(resultados):
    """Add found URLs to the autonomous learning queue."""
    if COLA_PATH.exists():
        with open(COLA_PATH, encoding='utf-8') as f:
            cola = json.load(f)
    else:
        cola = {"fuentes_pendientes": [], "procesadas": []}

    urls_existentes = {f['url'] for f in cola['fuentes_pendientes']}
    urls_existentes.update(cola['procesadas'])

    nuevas = 0
    for r in resultados:
        for url in r.get('urls', []):
            if url not in urls_existentes:
                cola['fuentes_pendientes'].append({
                    'url': url,
                    'patron_objetivo': r['patron'],
                    'tipo': r['tipo'],
                    'razon': r['razon'],
                    'prioridad': 'ALTA' if r['tipo'] == 'anomalia' else 'MEDIA',
                    'agregada': datetime.now().isoformat()
                })
                urls_existentes.add(url)
                nuevas += 1

    # Sort by priority
    cola['fuentes_pendientes'].sort(
        key=lambda x: (0 if x['prioridad'] == 'ALTA' else 1, x['agregada'])
    )

    with open(COLA_PATH, 'w', encoding='utf-8') as f:
        json.dump(cola, f, indent=2, ensure_ascii=False)

    return nuevas, len(cola['fuentes_pendientes'])


def generar_tarea_sincronicidad(brechas, queries):
    """Generate human-readable task for review."""
    if TAREAS_PATH.exists():
        with open(TAREAS_PATH, encoding='utf-8') as f:
            tareas = json.load(f)
    else:
        tareas = {"tareas": []}

    tareas["tareas"].append({
        "id": len(tareas["tareas"]) + 1,
        "categoria": "sincronicidad",
        "prioridad": "MEDIA",
        "emoji": "🔍",
        "descripcion": f"Sincronicidad: {len(brechas)} brechas detectadas, {len(queries)} queries generadas",
        "detalle": "Revisar cola_sincronicidad.json para ver URLs encontradas y aprobar integración",
        "brechas_top": [f"{b['wp']} → {b['ws']} ({b['n_src']} fuentes)" for b in brechas[:3]],
        "estado": "pendiente",
        "fecha": datetime.now().isoformat()
    })

    with open(TAREAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(tareas, f, indent=2, ensure_ascii=False)


# ── Reporte principal ─────────────────────────────────────────────────────────

def mostrar_reporte(brechas, puntos_ciegos, anomalias, queries):
    print("\n" + "=" * 65)
    print("  ANIMUS — MÓDULO DE SINCRONICIDAD")
    print("  Aprendizaje activo y dirigido")
    print("=" * 65)

    print(f"\n  📊 DIAGNÓSTICO ACTUAL")
    print(f"  Brechas detectadas (patrón fuerte, pocas fuentes): {len(brechas)}")
    print(f"  Tokens sin antecedente (puntos ciegos):            {len(puntos_ciegos)}")
    print(f"  Anomalías activas (contradicciones Kuhn):          {len(anomalias)}")

    print(f"\n  🔴 TOP BRECHAS — patrones que necesitan más fuentes:")
    for b in brechas[:6]:
        print(f"    {b['wp']:20} → {b['ws']:20} "
              f"fuerza:{b['fuerza']:.0f}  fuentes:{b['n_src']}")

    if anomalias:
        print(f"\n  ⚡ ANOMALÍAS ACTIVAS — contradicciones productivas:")
        EN_MAP = {
        'fracaso':'failure','colapso':'collapse','crisis':'crisis',
        'brecha':'gap','corrupción':'corruption','fraude':'fraud',
        'desigualdad':'inequality','regulación':'regulation',
        'algoritmo':'algorithm','reforma':'reform','desarrollo':'development',
        'educación':'education','cooperación':'cooperation','arquitectura':'architecture',
        'innovación':'innovation','política':'policy','transformación':'transformation',
    }
    for a in anomalias[:3]:
            print(f"    {a['wp']:20} → {a['ws']:20} "
                  f"confirman:{a['n_confirm']}  contradicen:{a['n_contradict']}")

    print(f"\n  🔍 QUERIES GENERADAS ({len(queries)} objetivos):")
    for q in queries:
        print(f"\n    [{q['tipo'].upper()}] {q['patron']}")
        print(f"    Razón: {q['razon'][:80]}...")
        for qs in q['queries'][:1]:
            print(f"    Query: \"{qs}\"")

    print(f"\n  Comandos:")
    print(f"  python sincronicidad.py --ejecutar   # Buscar URLs")
    print(f"  python sincronicidad.py --cola        # Ver cola")
    print()


def ver_cola():
    if not COLA_PATH.exists():
        print("  Cola vacía — ejecuta --ejecutar primero")
        return
    with open(COLA_PATH, encoding='utf-8') as f:
        cola = json.load(f)
    pendientes = cola.get('fuentes_pendientes', [])
    print(f"\n  Cola de sincronicidad: {len(pendientes)} fuentes pendientes\n")
    for i, f in enumerate(pendientes[:10], 1):
        print(f"  {i:2}. [{f['prioridad']}] {f['patron_objetivo']}")
        print(f"      {f['url'][:70]}")
        print(f"      Razón: {f['razon'][:60]}...")
        print()


# ── Main ──────────────────────────────────────────────────────────────────────


def modo_offline(queries):
    """Generate a ready-to-use search report when network is unavailable.
    Outputs queries formatted for manual execution and URL collection.
    """
    print("\n" + "=" * 65)
    print("  SINCRONICIDAD — MODO OFFLINE")
    print("  Red no disponible. Queries listas para ejecucion manual.")
    print("=" * 65)

    print("\n  Copia estas queries en tu navegador o en Claude.ai:")
    print("  Luego ejecuta: python sincronicidad.py --agregar-url URL patron")
    print()

    for i, q in enumerate(queries, 1):
        print(f"  [{i}] {q['tipo'].upper()} — {q['patron']}")
        print(f"  Razón: {q['razon'][:90]}")
        for qs in q['queries']:
            print(f"  🔍 {qs}")
        print()

    # Save queries to file for reference
    reporte = {
        'generado': datetime.now().isoformat(),
        'queries': queries,
        'instrucciones': (
            'Ejecuta cada query en Google/DuckDuckGo. '
            'Para cada URL relevante encontrada, ejecuta: '
            'python sincronicidad.py --agregar-url "URL" "patron"'
        )
    }
    Path("sincronicidad_queries.json").write_text(
        json.dumps(reporte, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    print("  Queries guardadas en sincronicidad_queries.json")


def agregar_url_manual(url, patron, tipo='manual'):
    """Manually add a URL to the synchronicity queue."""
    if COLA_PATH.exists():
        with open(COLA_PATH, encoding='utf-8') as f:
            cola = json.load(f)
    else:
        cola = {"fuentes_pendientes": [], "procesadas": []}

    urls_existentes = {f['url'] for f in cola['fuentes_pendientes']}
    urls_existentes.update(cola.get('procesadas', []))

    if url in urls_existentes:
        print(f"  URL ya existe en la cola: {url[:60]}")
        return

    cola['fuentes_pendientes'].append({
        'url': url,
        'patron_objetivo': patron,
        'tipo': tipo,
        'razon': f'Agregada manualmente para confirmar patron: {patron}',
        'prioridad': 'ALTA',
        'agregada': datetime.now().isoformat()
    })

    with open(COLA_PATH, 'w', encoding='utf-8') as f:
        json.dump(cola, f, indent=2, ensure_ascii=False)

    print(f"  ✅ URL agregada a la cola:")
    print(f"     {url[:70]}")
    print(f"     Patrón objetivo: {patron}")
    print(f"     Total en cola: {len(cola['fuentes_pendientes'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ejecutar", action="store_true",
                        help="Ejecutar búsquedas web y poblar cola")
    parser.add_argument("--cola", action="store_true",
                        help="Ver cola de fuentes pendientes")
    parser.add_argument("--agregar-url", type=str, default=None,
                        metavar="URL", help="Agregar URL manualmente a la cola")
    parser.add_argument("--patron", type=str, default="manual",
                        help="Patrón objetivo para la URL (usar con --agregar-url)")
    args = parser.parse_args()

    if args.cola:
        ver_cola()
        exit()

    if args.agregar_url:
        agregar_url_manual(args.agregar_url, args.patron)
        exit()

    with open(MEMORIA_PATH, encoding='utf-8') as f:
        memoria = json.load(f)

    brechas      = detectar_brechas(memoria)
    puntos_ciegos= detectar_puntos_ciegos(memoria)
    anomalias    = detectar_anomalias_activas(memoria)
    queries      = generar_queries(brechas, puntos_ciegos, anomalias)

    if args.ejecutar:
        # Try web search, fall back to offline mode
        try:
            import urllib.request
            urllib.request.urlopen('https://duckduckgo.com', timeout=3)
            resultados = ejecutar_busquedas(queries)
            nuevas, total = actualizar_cola(resultados)
            generar_tarea_sincronicidad(brechas, queries)
            print(f"\n  ✅ URLs nuevas agregadas a la cola: {nuevas}")
            print(f"  Total en cola: {total}")
            ver_cola()
        except Exception:
            modo_offline(queries)
    else:
        mostrar_reporte(brechas, puntos_ciegos, anomalias, queries)
