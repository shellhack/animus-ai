
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DECAY_RATE = 0.99       # per week — gentle decay
DECAY_FLOOR = 0.50      # connections never drop below 50% of original strength
MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"

def aplicar_decaimiento(memoria=None, verbose=True):
    """D09: Axelrod — recent interactions matter more than ancient ones.
    Apply gentle temporal decay to connections not recently reinforced.
    Connections confirmed by multiple sources decay much slower.
    """
    if memoria is None:
        with open(MEMORIA_PATH, encoding='utf-8') as f:
            memoria = json.load(f)

    conexiones = memoria['conexiones']
    ahora = datetime.now()
    decaidos = 0
    sin_fecha = 0

    # Count sources per connection for decay resistance
    conteo_fuentes = defaultdict(set)
    for k in conexiones:
        p = k.split('__>')
        if len(p) == 2:
            patron = f"{p[0].split('_')[-1]}__{p[1].split('_')[-1]}"
            src = p[0].split('_')[0]
            conteo_fuentes[patron].add(src)

    for k, v in list(conexiones.items()):
        if not isinstance(v, dict):
            # Old format — scalar value, no timestamp
            sin_fecha += 1
            continue

        if 'ultima_reforzada' not in v:
            continue

        ultima = datetime.fromisoformat(v['ultima_reforzada'])
        semanas = max(0, (ahora - ultima).days / 7)

        # Multi-source connections decay much slower
        patron = f"{k.split('__>')[0].split('_')[-1]}__{k.split('__>')[1].split('_')[-1]}" if '__>' in k else ''
        n_fuentes = len(conteo_fuentes.get(patron, set()))
        factor_fuentes = 1.0 + (n_fuentes * 0.1)  # More sources = slower decay
        semanas_efectivas = semanas / factor_fuentes

        factor = max(DECAY_FLOOR, DECAY_RATE ** semanas_efectivas)
        fuerza_efectiva = v['fuerza'] * factor
        if fuerza_efectiva != v.get('fuerza_efectiva'):
            v['fuerza_efectiva'] = round(fuerza_efectiva, 2)
            decaidos += 1

    if verbose:
        print(f"  [D09] Decaimiento aplicado: {decaidos} conexiones actualizadas")
        print(f"  [D09] Sin timestamp (formato antiguo): {sin_fecha} conexiones")

    return memoria


def migrar_a_formato_temporal(memoria=None, save=False):
    """Migrate old scalar connections to timestamped format.
    Only migrates connections that are currently scalars.
    """
    if memoria is None:
        with open(MEMORIA_PATH, encoding='utf-8') as f:
            memoria = json.load(f)

    ahora = datetime.now().isoformat()
    migradas = 0

    for k, v in list(memoria['conexiones'].items()):
        if isinstance(v, (int, float)):
            memoria['conexiones'][k] = {
                'fuerza': float(v),
                'fuerza_efectiva': float(v),
                'creada': ahora,
                'ultima_reforzada': ahora,
                'n_refuerzos': 1
            }
            migradas += 1

    print(f"  [D09] Migradas {migradas} conexiones al formato temporal")

    if save:
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(memoria, f, indent=2, ensure_ascii=False)
        print(f"  [D09] Guardado OK")

    return memoria


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ANIMUS D09 — Temporal Decay")
    parser.add_argument("--migrar", action="store_true",
                        help="Migrate connections to timestamped format")
    parser.add_argument("--decay", action="store_true",
                        help="Apply temporal decay to all connections")
    args = parser.parse_args()

    if args.migrar:
        migrar_a_formato_temporal(save=True)
    elif args.decay:
        mem = aplicar_decaimiento(verbose=True)
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
        print("  Guardado OK")
    else:
        print("  Uso: python temporal_decay.py --migrar | --decay")
        print("  Nota: La migracion convierte el formato de conexiones.")
        print("  Hacer backup de memoria_business.json antes de migrar.")
