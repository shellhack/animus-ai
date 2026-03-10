# -*- coding: utf-8 -*-
"""
D16 — Procesamiento Bilingüe Sistemático
Rastrea qué libros han sido procesados en qué idiomas
y calcula el delta bilingüe: patrones que solo emergen en un idioma.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORIA_PATH  = Path(__file__).parent / "memoria_business.json"
BILINGUAL_PATH = Path(__file__).parent / "bilingual_tracker.json"

# Known bilingual processing pairs: source_en → source_es
PARES_BILINGUES = {
    'klein':    'klein2',    # The Shock Doctrine
    'Fukuyama': 'libro',     # Origins of Political Order (partial)
}

# Books processed only in one language — candidates for bilingual processing
SOLO_EN = [
    'diamond',      # Guns, Germs and Steel
    'shirer',       # Rise and Fall of Third Reich
    'acemoglu',     # Why Nations Fail
    'graeber',      # Debt: First 5,000 Years
    'mitchell',     # Complexity: A Guided Tour
    'taleb',        # Antifragile
    'meadows',      # Thinking in Systems
    'axelrod',      # Evolution of Cooperation
]

SOLO_ES = []  # Books only in Spanish

def calcular_delta_bilingue(memoria, src_en, src_es):
    """Calculate patterns that only emerge in one language."""
    conexiones = memoria['conexiones']

    def get_patterns(src):
        pats = set()
        for k in conexiones:
            if k.startswith(src + '_'):
                p = k.split('__>')
                if len(p) == 2:
                    pats.add((p[0].split('_')[-1], p[1].split('_')[-1]))
        return pats

    pats_en = get_patterns(src_en)
    pats_es = get_patterns(src_es)

    solo_en  = pats_en - pats_es
    solo_es  = pats_es - pats_en
    comunes  = pats_en & pats_es

    return {
        'solo_en':  list(solo_en),
        'solo_es':  list(solo_es),
        'comunes':  list(comunes),
        'total_en': len(pats_en),
        'total_es': len(pats_es),
    }

def generar_reporte(memoria):
    print(f"\n{'='*65}")
    print(f"  D16 — ANÁLISIS BILINGÜE")
    print(f"{'='*65}")

    resultados = {}

    # Analyze known bilingual pairs
    for src_en, src_es in PARES_BILINGUES.items():
        delta = calcular_delta_bilingue(memoria, src_en, src_es)
        resultados[f"{src_en}/{src_es}"] = delta

        print(f"\n  Par bilingüe: {src_en} (EN) ↔ {src_es} (ES)")
        print(f"    Patrones solo en EN:  {delta['total_en']} total, {len(delta['solo_en'])} únicos")
        print(f"    Patrones solo en ES:  {delta['total_es']} total, {len(delta['solo_es'])} únicos")
        print(f"    Patrones comunes:     {len(delta['comunes'])}")
        ganancia = delta['total_es'] - delta['total_en']
        print(f"    Delta ES vs EN:       {'+' if ganancia >= 0 else ''}{ganancia} conexiones")

        if delta['solo_es']:
            print(f"    Puntos ciegos EN (solo emergen en ES):")
            for tp, ts in list(delta['solo_es'])[:4]:
                print(f"      {tp} → {ts}")

    print(f"\n  LIBROS CANDIDATOS PARA PROCESAMIENTO EN ESPAÑOL:")
    for libro in SOLO_EN:
        print(f"    📚 {libro} — solo procesado en inglés")
        print(f"       Comando: python process_book_v2.py \"[título_es].pdf\" memoria_business.json --nombre {libro}_es")

    print(f"\n  ESTIMACIÓN DE GANANCIA BILINGÜE:")
    if 'klein/klein2' in resultados:
        ratio = resultados['klein/klein2']['total_es'] / max(resultados['klein/klein2']['total_en'], 1)
        print(f"    Klein ratio ES/EN: {ratio:.1f}x ({resultados['klein/klein2']['total_en']} → {resultados['klein/klein2']['total_es']} conexiones)")
        est_total = sum(50 * ratio for _ in SOLO_EN)
        print(f"    Estimado si se procesan {len(SOLO_EN)} libros en ES: +{est_total:.0f} conexiones")

    Path(BILINGUAL_PATH).write_text(
        json.dumps({'fecha': datetime.now().isoformat(),
                    'pares': resultados,
                    'pendientes_es': SOLO_EN}, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    print(f"\n  Guardado: bilingual_tracker.json")

if __name__ == "__main__":
    with open(MEMORIA_PATH, encoding='utf-8') as f:
        mem = json.load(f)
    generar_reporte(mem)
