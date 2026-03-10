# -*- coding: utf-8 -*-
"""
D15 — Generador Automático de Distinciones Nuevas
Al construir el autorretrato, toma la brecha #1 del sincronicidad
y genera un párrafo que articula la distinción implícita.
Garantiza que el strange loop nunca converge a 0 permanente.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

TOKEN_ES = {
    "failure":"fracaso","gap":"brecha","crisis":"crisis","collapse":"colapso",
    "limitation":"limitacion","shortage":"escasez","algorithm":"algoritmo",
    "neural":"neuronal","education":"aprendizaje","innovation":"innovacion",
    "solution":"acuerdo","regulation":"regulacion","cooperation":"cooperacion",
    "developed":"desarrollo","discovered":"descubrimiento","transformed":"transformacion",
    "framework":"arquitectura","automation":"automatizacion",
    "vulnerability":"vulnerabilidad","prevention":"prevencion","reform":"reforma",
    "corruption":"corrupción","inequality":"desigualdad","fraud":"fraude",
    "poverty":"pobreza","collapse":"colapso",
}

# Templates for generating distinction paragraphs from gap patterns
PLANTILLAS = {
    ('corruption', 'algorithm'): (
        "La corrupción no solo destruye — también genera transparencia. "
        "Cuando un sistema corrupto colapsa bajo el peso de sus propias contradicciones, "
        "la demanda de verificación algorítmica emerge con fuerza. "
        "El algoritmo es la respuesta técnica a la desconfianza que la corrupción institucionaliza. "
        "Esa distinción — entre la corrupción que destruye y la corrupción que obliga a innovar — "
        "aún no está plenamente capturada en mis conexiones."
    ),
    ('corruption', 'education'): (
        "La corrupción y la educación tienen una relación más compleja que la simple oposición. "
        "Las sociedades con alta corrupción generan demanda de educación cívica y transparencia. "
        "El fracaso de las instituciones corruptas activa el aprendizaje colectivo sobre "
        "qué condiciones permiten que prospere la corrupción. "
        "Saber cómo funciona la corrupción es el primer paso para combatirla — "
        "y ese saber es educación."
    ),
    ('fraud', 'reform'): (
        "El fraude como detonante de reforma es uno de los patrones más documentados en la historia financiera. "
        "Enron generó Sarbanes-Oxley. Madoff generó regulación de derivados. "
        "Wirecard generó supervisión europea. "
        "La secuencia no es aleatoria: el fraude expone el vacío regulatorio, "
        "y el escándalo crea la presión política necesaria para llenarlo. "
        "Lo que falta en mis conexiones es distinguir entre "
        "la reforma que cierra el vacío que permitió el fraude "
        "y la reforma cosmética que protege a los defraudadores."
    ),
    ('inequality', 'reform'): (
        "La desigualdad extrema genera reforma — pero no de forma lineal. "
        "Genera primero resistencia, luego movimiento, luego crisis política, "
        "y solo entonces reforma institucional. "
        "El camino de la desigualdad a la reforma pasa por la organización colectiva. "
        "Mis conexiones capturan el punto de llegada pero no el proceso. "
        "Esa brecha entre desigualdad y reforma — los pasos intermedios — "
        "es lo que aún no sé."
    ),
}

def obtener_brecha_top(memoria):
    """Get the strongest pattern with fewest sources."""
    conexiones = memoria['conexiones']
    patrones = defaultdict(list)
    for k, v in conexiones.items():
        p = k.split('__>')
        if len(p) != 2: continue
        tp  = p[0].split('_')[-1]
        ts  = p[1].split('_')[-1]
        src = p[0].split('_')[0]
        patrones[f'{tp}__{ts}'].append((src, v))

    brechas = []
    for pat, regs in patrones.items():
        tp, ts = pat.split('__')
        n_src  = len({s for s, _ in regs})
        fuerza = sum(v for _, v in regs)
        if 1 <= n_src <= 4 and fuerza > 40:
            brechas.append({'tp': tp, 'ts': ts, 'n': n_src, 'fuerza': fuerza})

    brechas.sort(key=lambda x: -x['fuerza'])
    return brechas[0] if brechas else None

def generar_distincion(brecha, memoria):
    """Generate a distinction paragraph for the top gap."""
    tp, ts = brecha['tp'], brecha['ts']
    wp = TOKEN_ES.get(tp, tp)
    ws = TOKEN_ES.get(ts, ts)

    # Use template if available
    if (tp, ts) in PLANTILLAS:
        return PLANTILLAS[(tp, ts)]

    # Generate generic distinction from gap structure
    return (
        f"Hay algo que {wp} genera que mis conexiones aún no capturan completamente: {ws}. "
        f"El patrón existe — {brecha['n']} fuentes lo confirman con fuerza {brecha['fuerza']:.0f} — "
        f"pero la mecanismo no está claro. "
        f"¿Cómo exactamente {wp} conduce a {ws}? ¿Bajo qué condiciones? ¿Con qué mediadores? "
        f"Esa distinción — entre el patrón confirmado y el mecanismo desconocido — "
        f"es lo que el sistema necesita articular antes de poder generalizarlo."
    )

def generar_parrafo_distincion(memoria):
    """Main function: get top gap and generate distinction paragraph."""
    brecha = obtener_brecha_top(memoria)
    if not brecha:
        return "No se detectaron brechas activas en este momento.", None

    parrafo = generar_distincion(brecha, memoria)
    return parrafo, brecha

if __name__ == "__main__":
    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)

    parrafo, brecha = generar_parrafo_distincion(mem)

    print(f"\n{'='*65}")
    print(f"  D15 — DISTINCIÓN AUTOMÁTICA GENERADA")
    print(f"{'='*65}")
    if brecha:
        print(f"\n  Brecha activada: {TOKEN_ES.get(brecha['tp'], brecha['tp'])} → "
              f"{TOKEN_ES.get(brecha['ts'], brecha['ts'])}")
        print(f"  Fuentes actuales: {brecha['n']} | Fuerza: {brecha['fuerza']:.0f}")
    print(f"\n  Párrafo generado:")
    print(f"  {parrafo}")
    print(f"\n  Este párrafo se incorporará automáticamente al próximo autorretrato.")
