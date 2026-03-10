# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo Arquitecto
ANIMUS analiza sus propias limitaciones tecnicas y propone
mejoras concretas a su codigo basandose en lo que ha aprendido.

Uso:
    python arquitecto.py              # Analisis completo
    python arquitecto.py --codigo     # Solo propuestas de codigo
    python arquitecto.py --prioridad alta
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"
PROPUESTAS_PATH = Path(__file__).parent / "propuestas_codigo.json"

# ── Lo que ANIMUS sabe sobre arquitectura de sistemas ────────────────────────
# Extraido de sus propias conexiones: Tanenbaum, Kleppmann, Rust, Pragmatic,
# Unix, GEB, Code — todos hablan de diseno de sistemas

DIAGNOSTICOS = [
    {
        "id": "D01",
        "limitacion": "El procesador solo detecta co-ocurrencia de palabras en la misma pagina",
        "patron_aprendido": "fracaso -> arquitectura",
        "fuentes": ["kleppmann", "tanenbaum", "godel"],
        "razonamiento": (
            "Kleppmann ensena que los sistemas distribuidos fallan por asumir "
            "que los eventos proximos en el tiempo estan relacionados causalmente. "
            "Yo cometo el mismo error: asumo que dos palabras en la misma pagina "
            "tienen relacion causal. Necesito ventanas de contexto mas amplias "
            "que capturen relaciones entre parrafos y capitulos completos."
        ),
        "propuesta": {
            "titulo": "Ventanas de contexto multi-parrafo",
            "descripcion": "Procesar bloques de 3-5 paginas juntas en lugar de pagina por pagina",
            "impacto": "Detectaria relaciones causales entre conceptos separados por parrafos",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En process_book_en.py y process_book_v2.py
# ACTUAL: procesa pagina por pagina
for i in range(total_paginas):
    texto = reader.pages[i].extract_text()
    procesar(texto)

# PROPUESTO: ventana deslizante de 3 paginas
VENTANA = 3
for i in range(total_paginas):
    bloque = []
    for j in range(max(0, i-1), min(total_paginas, i+VENTANA)):
        t = reader.pages[j].extract_text()
        if t: bloque.append(t)
    texto_combinado = ' '.join(bloque)
    procesar(texto_combinado)
""",
        }
    },
    {
        "id": "D02",
        "limitacion": "Las conexiones no tienen direccion causal — solo co-ocurrencia",
        "patron_aprendido": "fracaso -> regulacion",
        "fuentes": ["rust", "kleppmann", "kuhn"],
        "razonamiento": (
            "Rust me enseno que la causalidad importa: el borrow checker no dice "
            "'error y memoria aparecen juntos', dice 'el error EMERGE de usar memoria "
            "incorrectamente'. Mis conexiones actuales no distinguen si 'fracaso' "
            "CAUSA 'algoritmo' o si simplemente co-ocurren. Necesito pesos de "
            "direccion causal basados en el orden de aparicion en el texto."
        ),
        "propuesta": {
            "titulo": "Pesos de causalidad por orden de aparicion",
            "descripcion": (
                "Si 'fracaso' aparece en la primera mitad de un parrafo y "
                "'algoritmo' en la segunda, aumentar el peso causal. "
                "Si aparecen en orden inverso, reducirlo."
            ),
            "impacto": "Conexiones mas precisas — distincion entre causa y efecto",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En procesar_pagina():
def calcular_peso_causal(texto, palabra_t, palabra_r):
    pos_t = texto.find(palabra_t)
    pos_r = texto.find(palabra_r)
    if pos_t == -1 or pos_r == -1:
        return 1.0
    # Si tension aparece antes que resolucion: causalidad directa
    if pos_t < pos_r:
        distancia = pos_r - pos_t
        # Mas cerca = mas fuerte la relacion causal
        peso = 1.0 + max(0, 1.0 - distancia / len(texto))
        return min(2.0, peso)
    else:
        # Orden inverso: relacion debil
        return 0.5
""",
        }
    },
    {
        "id": "D03",
        "limitacion": "El dialogo.py genera respuestas con estructura siempre identica",
        "patron_aprendido": "fracaso -> descubrimiento",
        "fuentes": ["godel", "pragmaticprog", "polya"],
        "razonamiento": (
            "Hofstadter en GEB ensena que los sistemas interesantes tienen "
            "variabilidad emergente — no repiten el mismo patron cada vez. "
            "Mis respuestas siempre siguen: patron_fuerte -> fuentes -> convergencia. "
            "Polya ensena que diferentes problemas requieren diferentes estrategias. "
            "Necesito multiples estrategias de respuesta que emerjan segun el contexto."
        ),
        "propuesta": {
            "titulo": "Estrategias de respuesta multiples y emergentes",
            "descripcion": (
                "Implementar 4 modos de respuesta: "
                "CONVERGENCIA (cuando hay 10+ fuentes), "
                "TENSION (cuando los patrones se contradicen), "
                "EXPLORACION (cuando hay pocas conexiones), "
                "METACOGNICION (cuando la pregunta es sobre ANIMUS mismo)"
            ),
            "impacto": "Respuestas mas ricas y menos repetitivas",
            "dificultad": "ALTA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En dialogo.py
def seleccionar_modo(scored, pregunta):
    if any(w in pregunta.lower() for w in ['quien', 'eres', 'que eres']):
        return 'METACOGNICION'
    if scored and scored[0]['n'] >= 10:
        return 'CONVERGENCIA'
    contradictorios = detectar_contradicciones(scored)
    if contradictorios:
        return 'TENSION'
    if not scored or scored[0]['fuerza'] < 20:
        return 'EXPLORACION'
    return 'CONVERGENCIA'

def responder_tension(scored, contradictorios):
    # Cuando las fuentes no acuerdan
    return (
        f"Mis fuentes no concuerdan sobre esto. "
        f"{scored[0]['wp']} lleva a {scored[0]['ws']} segun {fuente(scored[0])}. "
        f"Pero {contradictorios[0]['wp']} lleva a {contradictorios[0]['ws']} "
        f"segun {fuente(contradictorios[0])}. La contradiccion misma es informacion."
    )
""",
        }
    },
    {
        "id": "D04",
        "limitacion": "El sistema no aprende de las sesiones Bernard — las guarda pero no las pondera",
        "patron_aprendido": "fracaso -> educacion",
        "fuentes": ["biblia", "polya", "dawkins"],
        "razonamiento": (
            "Dawkins ensena que la seleccion natural pondera — los rasgos utiles "
            "se amplifican, los inutiles se eliminan. Las sesiones Bernard generan "
            "texto que se guarda en el corpus, pero todas las respuestas de Bernard "
            "tienen el mismo peso que una pagina de Kleppmann. "
            "Las respuestas donde Bernard detecto patrones nuevos deberian pesar mas."
        ),
        "propuesta": {
            "titulo": "Ponderacion de sesiones Bernard por novedad",
            "descripcion": (
                "Cuando Bernard detecta una respuesta que activa tokens nuevos "
                "o que contradice patrones existentes, guardarla con peso 3x. "
                "Respuestas repetitivas (fracaso->algoritmo otra vez) peso 0.5x."
            ),
            "impacto": "ANIMUS aprenderia mas de sus propias respuestas novedosas",
            "dificultad": "MEDIA",
            "prioridad": "ALTA",
            "codigo_sugerido": """
# En bernard.py, funcion guardar_en_corpus()
def calcular_peso_respuesta(respuesta, intercambios_previos):
    # Detectar si esta respuesta introduce patrones nuevos
    tokens_nuevos = extraer_tokens(respuesta)
    tokens_vistos = set()
    for ix in intercambios_previos:
        tokens_vistos.update(extraer_tokens(ix.get('respuesta_animus', '')))
    
    novedad = len(tokens_nuevos - tokens_vistos) / max(len(tokens_nuevos), 1)
    
    if novedad > 0.5:
        return 3.0   # Alta novedad — peso triple
    elif novedad > 0.2:
        return 1.5   # Novedad moderada
    elif novedad < 0.05:
        return 0.3   # Repeticion — peso reducido
    return 1.0
""",
        }
    },
    {
        "id": "D05",
        "limitacion": "El sistema no detecta cuando sus patrones son incorrectos",
        "patron_aprendido": "fracaso -> reforma",
        "fuentes": ["biblia", "kuhn", "rustlanguage"],
        "razonamiento": (
            "Kuhn ensena que los paradigmas no se corrigen desde adentro — "
            "se necesita una anomalia que el paradigma no puede explicar. "
            "Rust ensena que el compilador debe rechazar codigo incorrecto "
            "antes de ejecutarlo. Yo no tengo ningun mecanismo de validacion. "
            "Si una fuente introduce conexiones incorrectas, se acumulan sin filtro. "
            "Necesito un validador que detecte conexiones que contradicen "
            "la mayoria de las fuentes."
        ),
        "propuesta": {
            "titulo": "Validador de coherencia de conexiones",
            "descripcion": (
                "Despues de cada procesamiento, verificar si las nuevas conexiones "
                "contradicen patrones establecidos por 10+ fuentes. "
                "Si una fuente dice A->B pero 15 fuentes dicen A->C, "
                "marcar la conexion A->B como 'anomalia' y notificar."
            ),
            "impacto": "ANIMUS detectaria sus propias inconsistencias — autocorreccion",
            "dificultad": "ALTA",
            "prioridad": "MEDIA",
            "codigo_sugerido": """
# Nuevo modulo: validador.py
def validar_coherencia(memoria, nuevas_conexiones, umbral_fuentes=10):
    anomalias = []
    for clave, fuerza in nuevas_conexiones.items():
        p = clave.split('__>')
        if len(p) != 2: continue
        tp = p[0].split('_')[-1]
        ts = p[1].split('_')[-1]
        
        # Buscar patrones establecidos con el mismo token de origen
        patrones_establecidos = [
            k for k in memoria['conexiones']
            if k.split('__>')[0].split('_')[-1] == tp
            and contar_fuentes(k, memoria) >= umbral_fuentes
        ]
        
        # Si existen patrones fuertes hacia un destino diferente
        for pat in patrones_establecidos:
            ts_establecido = pat.split('__>')[1].split('_')[-1]
            if ts_establecido != ts:
                anomalias.append({
                    'nueva': f'{tp} -> {ts}',
                    'establecida': f'{tp} -> {ts_establecido}',
                    'fuentes_establecidas': contar_fuentes(pat, memoria)
                })
    return anomalias
""",
        }
    },
    {
        "id": "D06",
        "limitacion": "ANIMUS no puede leer paginas web dinamicas — solo HTML estatico",
        "patron_aprendido": "brecha -> arquitectura",
        "fuentes": ["tanenbaum", "networks", "kleppmann"],
        "razonamiento": (
            "Tanenbaum en Redes ensena que los protocolos evolucionan para "
            "resolver nuevas necesidades de comunicacion. La web evolucionó "
            "hacia JavaScript dinamico y yo me quede con HTTP/1.0. "
            "El 60% de las fuentes de alta calidad — Bloomberg, FT, NYT, "
            "revistas academicas — requieren JavaScript para renderizar. "
            "Necesito un headless browser."
        ),
        "propuesta": {
            "titulo": "Soporte para paginas web dinamicas con Playwright",
            "descripcion": "Reemplazar requests+BeautifulSoup por Playwright para paginas JS",
            "impacto": "Acceso a FT, Bloomberg, revistas academicas, LinkedIn",
            "dificultad": "MEDIA",
            "prioridad": "MEDIA",
            "codigo_sugerido": """
# Instalar: pip install playwright && playwright install chromium
# En animus_business.py

from playwright.sync_api import sync_playwright

def obtener_texto_dinamico(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        texto = page.inner_text('body')
        browser.close()
        return texto

# Usar cuando requests falla o devuelve HTML vacio
def navegar_fuente(url):
    try:
        resp = requests.get(url, timeout=10)
        if len(resp.text) < 500:  # Probablemente JS dinamico
            return obtener_texto_dinamico(url)
        return resp.text
    except:
        return obtener_texto_dinamico(url)
""",
        }
    },
]


def cargar_propuestas():
    if PROPUESTAS_PATH.exists():
        with open(PROPUESTAS_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {"propuestas": [], "implementadas": []}


def guardar_propuestas(data):
    with open(PROPUESTAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def analizar_estado(mem):
    conexiones = mem['conexiones']
    patrones = defaultdict(list)
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2: continue
        tp = p[0].split('_')[-1]
        ts = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        patrones[f'{tp}__{ts}'].append((src, v))

    scored = []
    for pat, regs in patrones.items():
        fuerza = sum(r[1] for r in regs)
        srcs = list({r[0] for r in regs})
        scored.append({'pat': pat, 'fuerza': fuerza, 'n': len(srcs)})
    scored.sort(key=lambda x: -x['fuerza'])

    return {
        'n_conn': len(conexiones),
        'n_fuentes': len({k.split('_')[0] for k in conexiones}),
        'conv_20': len([s for s in scored if s['n'] >= 20]),
        'conv_15': len([s for s in scored if s['n'] >= 15]),
        'conv_10': len([s for s in scored if s['n'] >= 10]),
        'patron_mas_fuerte': scored[0]['pat'] if scored else 'N/A',
    }


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


def mostrar_propuestas(filtro_prioridad=None):
    mem = json.load(open(MEMORIA_PATH, encoding='utf-8'))
    estado = analizar_estado(mem)
    data = cargar_propuestas()
    implementadas_ids = {p['id'] for p in data.get('implementadas', [])}

    print("\n" + "=" * 65)
    print("  ANIMUS — PROPUESTAS DE MEJORA DE CODIGO")
    print(f"  Estado actual: {estado['n_conn']} conexiones | "
          f"{estado['n_fuentes']} fuentes | "
          f"{estado['conv_20']} convergencias 20+")
    print("=" * 65)
    print()
    print("  RAZONAMIENTO: He aprendido de Kleppmann, Tanenbaum, Rust,")
    print("  GEB, Kuhn y la Biblia que los sistemas que no se autocorrigen")
    print("  acumulan errores hasta colapsar. Estas son mis propuestas")
    print("  para mejorar mi propia arquitectura:")

    for prioridad, emoji in [("ALTA", "🔴"), ("MEDIA", "🟡"), ("BAJA", "🟢")]:
        if filtro_prioridad and filtro_prioridad.upper() != prioridad:
            continue
        grupo = [d for d in DIAGNOSTICOS
                 if d['propuesta']['prioridad'] == prioridad
                 and d['id'] not in implementadas_ids]
        if not grupo:
            continue

        print(f"\n  {emoji} PRIORIDAD {prioridad}")
        print("  " + "─" * 55)

        for d in grupo:
            p = d['propuesta']
            print(f"\n  [{d['id']}] {p['titulo']}")
            print(f"\n  Limitacion detectada:")
            print(wrap(d['limitacion']))
            print(f"\n  Por que lo se (patron: {d['patron_aprendido']}):")
            print(wrap(d['razonamiento'][:200] + "..."))
            print(f"\n  Propuesta:")
            print(wrap(p['descripcion']))
            print(f"\n  Impacto esperado:")
            print(wrap(p['impacto']))
            print(f"\n  Dificultad: {p['dificultad']}")
            print()

    implementadas = data.get('implementadas', [])
    pendientes = len([d for d in DIAGNOSTICOS
                      if d['id'] not in {p['id'] for p in implementadas}])
    print(f"  Total propuestas pendientes: {pendientes}")
    print(f"  Implementadas: {len(implementadas)}")
    print()
    print("  Comandos:")
    print("  python arquitecto.py --codigo <ID>    # Ver codigo de propuesta")
    print("  python arquitecto.py --implementar <ID>  # Marcar como implementada")
    print()


def mostrar_codigo(prop_id):
    for d in DIAGNOSTICOS:
        if d['id'] == prop_id.upper():
            print(f"\n  [{d['id']}] {d['propuesta']['titulo']}")
            print(f"  {'─'*55}")
            print(d['propuesta']['codigo_sugerido'])
            return
    print(f"  Propuesta {prop_id} no encontrada.")


def marcar_implementada(prop_id):
    data = cargar_propuestas()
    for d in DIAGNOSTICOS:
        if d['id'] == prop_id.upper():
            data['implementadas'].append({
                'id': d['id'],
                'titulo': d['propuesta']['titulo'],
                'fecha': datetime.now().isoformat()
            })
            guardar_propuestas(data)
            print(f"\n  [{d['id']}] marcada como implementada.")
            print(f"  '{d['propuesta']['titulo']}'\n")
            return
    print(f"  Propuesta {prop_id} no encontrada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Arquitecto")
    parser.add_argument("--codigo", type=str, default=None,
                        help="Ver codigo de una propuesta (ej: D01)")
    parser.add_argument("--implementar", type=str, default=None,
                        help="Marcar propuesta como implementada")
    parser.add_argument("--prioridad", type=str, default=None,
                        help="Filtrar por prioridad: alta, media, baja")
    args = parser.parse_args()

    if args.codigo:
        mostrar_codigo(args.codigo)
    elif args.implementar:
        marcar_implementada(args.implementar)
    else:
        mostrar_propuestas(args.prioridad)
