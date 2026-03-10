"""
ANIMUS — Loop Autónomo Completo
Ciclo de automejora que corre indefinidamente:

  1. Introspección  — detecta brechas propias
  2. Automejora     — expande vocabulario y fuentes
  3. Entrenamiento  — aprende 500 páginas nuevas
  4. Validación     — cruza con Google Trends
  5. Reporte        — genera PDF con lo aprendido
  6. Espera         — hasta el próximo ciclo

Uso:
    python autonomous_loop.py                    # Ciclo único
    python autonomous_loop.py --continuo         # Loop infinito (semanal)
    python autonomous_loop.py --continuo --dias 3 # Cada 3 días
    python autonomous_loop.py --dry-run          # Simulación
"""

import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR     = Path(__file__).parent
MEMORIA_PATH = BASE_DIR / "memoria_business.json"
LOG_PATH     = BASE_DIR / "autonomous_loop.log"
STATE_PATH   = BASE_DIR / "loop_state.json"
PYTHON       = sys.executable

import os
ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ──────────────────────────────────────────────────────────────────────────────
# STATE — tracks cycles and progress
# ──────────────────────────────────────────────────────────────────────────────

def load_state():
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {
        "ciclo": 0,
        "ultimo_ciclo": None,
        "palabras_inicio": 0,
        "conexiones_inicio": 0,
        "historial": [],
    }

def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def mem_stats():
    if not MEMORIA_PATH.exists():
        return 0, 0
    with open(MEMORIA_PATH, encoding="utf-8") as f:
        m = json.load(f)
    return len(m.get("conexiones", {})), len(m.get("lenguaje", {}))

# ──────────────────────────────────────────────────────────────────────────────
# STEPS
# ──────────────────────────────────────────────────────────────────────────────

def run_step(name, cmd, dry_run=False):
    """Run a subprocess step, return success bool."""
    log(f"STEP — {name}")
    if dry_run:
        log(f"  [DRY-RUN] Would run: {' '.join(str(c) for c in cmd)}")
        return True

    start = time.time()
    result = subprocess.run(
        cmd, cwd=BASE_DIR,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env=ENV
    )
    elapsed = int(time.time() - start)

    # Print relevant output lines
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line and any(k in line for k in [
            "Vocabulario", "conexiones", "palabras", "Total",
            "Fuentes", "agregadas", "WARNING", "Error",
            "complete", "generado", "actualizada", "Ciclo",
            "STEP", "OK", "palabras nuevas", "Conexiones"
        ]):
            log(f"  {line}")

    if result.returncode != 0:
        log(f"  ERROR ({elapsed}s): {result.stderr[-200:]}", "ERROR")
        return False

    log(f"  OK ({elapsed}s)")
    return True


def step_introspect(dry_run=False):
    return run_step(
        "Introspección activa",
        [PYTHON, str(BASE_DIR / "introspection.py"), "--plan"],
        dry_run
    )


def step_tareas(dry_run=False):
    """ANIMUS generates new tasks for Ernesto based on its gaps."""
    return run_step(
        "Generacion de tareas para Ernesto",
        [PYTHON, str(BASE_DIR / "tareas.py"), "--generar"],
        dry_run
    )


def step_bernard(n_preguntas=15, dry_run=False):
    """Bernard interviews ANIMUS before training — saves to corpus."""
    import random
    temas = ["filosofia", "limitaciones", "aprendizaje", "futuro", "meta"]
    tema = temas[datetime.now().isocalendar()[1] % len(temas)]  # rotates weekly
    return run_step(
        f"Protocolo Bernard — {n_preguntas} preguntas (tema: {tema})",
        [PYTHON, str(BASE_DIR / "bernard.py"), "--auto", str(n_preguntas),
         "--tema", tema],
        dry_run
    )


def step_improve(dry_run=False):
    return run_step(
        "Automejora (vocabulario + fuentes)",
        [PYTHON, str(BASE_DIR / "automejora.py")],
        dry_run
    )


def step_train(pages=500, dry_run=False):
    return run_step(
        f"Entrenamiento ({pages} páginas)",
        [PYTHON, str(BASE_DIR / "animus_business.py"), str(pages)],
        dry_run
    )


def step_validate(dry_run=False):
    trends_cache = BASE_DIR / "trends_cache.json"
    if trends_cache.exists() and not dry_run:
        trends_cache.unlink()
        log("  Cache de Trends limpiado")

    return run_step(
        "Validación con Google Trends",
        [PYTHON, str(BASE_DIR / "trends_validator.py"), "--report"],
        dry_run
    )


def step_report(ciclo, dry_run=False):
    date_str = datetime.now().strftime("%Y_%m_%d")
    reports_dir = BASE_DIR / "reports"
    if not dry_run:
        reports_dir.mkdir(exist_ok=True)
    output = reports_dir / f"ANIMUS_Ciclo_{ciclo:03d}_{date_str}.pdf"

    ok = run_step(
        "Generación de reporte semanal",
        [PYTHON, str(BASE_DIR / "generate_report.py"), str(output)],
        dry_run
    )

    # Also generate self-awareness report
    output_ac = reports_dir / f"ANIMUS_Autoconciencia_{ciclo:03d}_{date_str}.pdf"
    run_step(
        "Reporte de autoconciencia",
        [PYTHON, str(BASE_DIR / "reporte_autoconciencia.py"), str(output_ac)],
        dry_run
    )

    return ok, output if not dry_run else None


# ──────────────────────────────────────────────────────────────────────────────
# SINGLE CYCLE
# ──────────────────────────────────────────────────────────────────────────────

def run_cycle(ciclo, pages=500, dry_run=False):
    start = time.time()
    conn_before, vocab_before = mem_stats()

    log("")
    log("=" * 60)
    log(f"  ANIMUS — CICLO AUTÓNOMO #{ciclo}")
    log(f"  {datetime.now().strftime('%A, %d de %B de %Y — %H:%M')}")
    log(f"  Estado: {conn_before} conexiones | {vocab_before} palabras")
    log("=" * 60)

    results = {}

    # 1. Introspect
    results["introspect"] = step_introspect(dry_run)

    # 2. Bernard — interview before training (saves to corpus)
    results["bernard"] = step_bernard(15, dry_run)

    # 3. Self-improve
    results["improve"] = step_improve(dry_run)

    # 4. Train (includes Bernard corpus + expanded vocab)
    results["train"] = step_train(pages, dry_run)

    # 5. Validate
    results["validate"] = step_validate(dry_run)

    # 6. Report
    results["report"], report_path = step_report(ciclo, dry_run)

    # 7. Generate tasks for Ernesto
    results["tareas"] = step_tareas(dry_run)

    # Final stats
    conn_after, vocab_after = mem_stats()
    elapsed = int(time.time() - start)

    delta_conn  = conn_after - conn_before
    delta_vocab = vocab_after - vocab_before

    log("")
    log("=" * 60)
    log(f"  CICLO #{ciclo} COMPLETADO")
    log(f"  Duración:    {elapsed // 60}m {elapsed % 60}s")
    log(f"  Conexiones:  {conn_before} → {conn_after} (+{delta_conn})")
    log(f"  Vocabulario: {vocab_before} → {vocab_after} (+{delta_vocab})")
    if report_path:
        log(f"  Reporte:     {report_path.name}")
    steps_ok = sum(1 for v in results.values() if v)
    log(f"  Pasos OK:    {steps_ok}/{len(results)}")
    log("=" * 60)
    log("")

    return {
        "ciclo": ciclo,
        "fecha": datetime.now().isoformat(),
        "duracion_s": elapsed,
        "conn_antes": conn_before,
        "conn_despues": conn_after,
        "vocab_antes": vocab_before,
        "vocab_despues": vocab_after,
        "delta_conn": delta_conn,
        "delta_vocab": delta_vocab,
        "pasos_ok": steps_ok,
        "total_pasos": len(results),
    }


# ──────────────────────────────────────────────────────────────────────────────
# CONTINUOUS LOOP
# ──────────────────────────────────────────────────────────────────────────────

def loop_continuo(intervalo_dias=7, pages=500, dry_run=False):
    state = load_state()

    log("ANIMUS — LOOP AUTÓNOMO INICIADO")
    log(f"Intervalo: cada {intervalo_dias} días")
    log(f"Páginas por ciclo: {pages}")
    log("Presiona Ctrl+C para detener\n")

    try:
        while True:
            ciclo = state["ciclo"] + 1

            # Run cycle
            resultado = run_cycle(ciclo, pages, dry_run)

            # Update state
            state["ciclo"] = ciclo
            state["ultimo_ciclo"] = datetime.now().isoformat()
            state["historial"].append(resultado)

            # Keep only last 52 cycles (1 year)
            if len(state["historial"]) > 52:
                state["historial"] = state["historial"][-52:]

            save_state(state)

            if dry_run:
                log("DRY-RUN completado. Saliendo.")
                break

            # Schedule next cycle
            proximo = datetime.now() + timedelta(days=intervalo_dias)
            log(f"Próximo ciclo: {proximo.strftime('%A %d de %B a las %H:%M')}")
            log(f"Esperando {intervalo_dias * 24} horas...")

            # Sleep in small chunks so Ctrl+C works
            total_seconds = intervalo_dias * 24 * 3600
            for _ in range(total_seconds):
                time.sleep(1)

    except KeyboardInterrupt:
        log("\nLoop detenido por el usuario.")
        save_state(state)


# ──────────────────────────────────────────────────────────────────────────────
# PROGRESS DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────

def mostrar_progreso():
    state = load_state()
    conn, vocab = mem_stats()

    print("\n" + "=" * 60)
    print("  ANIMUS — DASHBOARD DE PROGRESO")
    print("=" * 60)
    print(f"  Ciclos completados: {state['ciclo']}")
    print(f"  Último ciclo:       {state.get('ultimo_ciclo', 'Nunca')[:19]}")
    print(f"  Conexiones actuales: {conn}")
    print(f"  Vocabulario actual:  {vocab}")

    if state["historial"]:
        print("\n  Últimos 5 ciclos:")
        print(f"  {'Ciclo':6} {'Fecha':12} {'Conn':6} {'Vocab':6} {'Duración':10}")
        print("  " + "-" * 46)
        for h in state["historial"][-5:]:
            fecha = h["fecha"][:10]
            dur = f"{h['duracion_s']//60}m{h['duracion_s']%60}s"
            print(f"  #{h['ciclo']:<5} {fecha:12} "
                  f"+{h['delta_conn']:<5} +{h['delta_vocab']:<5} {dur}")

        # Growth trend
        if len(state["historial"]) >= 2:
            avg_conn  = sum(h["delta_conn"]  for h in state["historial"]) / len(state["historial"])
            avg_vocab = sum(h["delta_vocab"] for h in state["historial"]) / len(state["historial"])
            print(f"\n  Promedio por ciclo: +{avg_conn:.0f} conexiones, +{avg_vocab:.0f} palabras")

            # Project 1 year
            ciclos_restantes = 52 - state["ciclo"]
            if ciclos_restantes > 0:
                proj_conn  = conn  + int(avg_conn  * ciclos_restantes)
                proj_vocab = vocab + int(avg_vocab * ciclos_restantes)
                print(f"  Proyección 1 año:   ~{proj_conn} conexiones, ~{proj_vocab} palabras")

    print("=" * 60 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Autonomous Loop")
    parser.add_argument("--continuo",  action="store_true",
                        help="Loop infinito")
    parser.add_argument("--dias",      type=int, default=7,
                        help="Intervalo entre ciclos en días (default: 7)")
    parser.add_argument("--paginas",   type=int, default=500,
                        help="Páginas por ciclo (default: 500)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Simulación sin modificar nada")
    parser.add_argument("--progreso",  action="store_true",
                        help="Muestra dashboard de progreso")
    args = parser.parse_args()

    if args.progreso:
        mostrar_progreso()
        sys.exit(0)

    if not MEMORIA_PATH.exists():
        print(f"ERROR: {MEMORIA_PATH} no encontrado.")
        sys.exit(1)

    if args.continuo:
        loop_continuo(args.dias, args.paginas, args.dry_run)
    else:
        # Single cycle
        state = load_state()
        ciclo = state["ciclo"] + 1
        resultado = run_cycle(ciclo, args.paginas, args.dry_run)
        state["ciclo"] = ciclo
        state["ultimo_ciclo"] = datetime.now().isoformat()
        state["historial"].append(resultado)
        save_state(state)
        mostrar_progreso()


# ── D12: Circuit Breaker ─────────────────────────────────────────────────────
# Taleb: fragile systems fail catastrophically without stop mechanisms
# Rust: the compiler rejects the whole program if memory safety is violated

UMBRAL_ANOMALIAS = 0.30  # 30% anomaly rate triggers circuit breaker

def circuit_breaker(nuevas_conexiones, memoria_actual, nombre_fuente):
    """D12: Pause integration if anomaly rate exceeds threshold."""
    if not nuevas_conexiones:
        return True, memoria_actual

    try:
        from validador import detectar_anomalias, construir_indice
        from collections import defaultdict

        anomalias = detectar_anomalias(
            memoria_actual['conexiones'],
            memoria_actual['lenguaje'],
            umbral_fuentes=5
        )
        # Count anomalies from this specific source
        anomalias_fuente = [
            a for a in anomalias
            if nombre_fuente in a.get('fuentes_anomalas', [])
        ]
        tasa = len(anomalias_fuente) / max(len(nuevas_conexiones), 1)

        if tasa > UMBRAL_ANOMALIAS:
            print(f"\n  ⚡ CIRCUIT BREAKER ACTIVADO")
            print(f"  Fuente: {nombre_fuente}")
            print(f"  Anomalias detectadas: {len(anomalias_fuente)} / {len(nuevas_conexiones)} conexiones nuevas")
            print(f"  Tasa: {tasa:.0%} > umbral {UMBRAL_ANOMALIAS:.0%}")
            print(f"  Integracion pausada. Generando tarea para revision humana...")

            # Generate quarantine task
            _generar_tarea_cuarentena(nombre_fuente, tasa, anomalias_fuente[:3])
            return False, None

        if tasa > 0.10:
            print(f"  ⚠️  Alerta: {tasa:.0%} de anomalias en '{nombre_fuente}' — dentro del umbral")

        return True, memoria_actual

    except Exception as e:
        print(f"  [Circuit Breaker] Error: {e} — permitiendo integracion")
        return True, memoria_actual


def _generar_tarea_cuarentena(fuente, tasa, anomalias_muestra):
    """Generate a human review task for quarantined source."""
    from pathlib import Path
    import json
    from datetime import datetime

    tareas_path = Path(__file__).parent / "tareas_pendientes.json"
    if tareas_path.exists():
        with open(tareas_path, encoding='utf-8') as f:
            tareas = json.load(f)
    else:
        tareas = {"tareas": []}

    tareas["tareas"].append({
        "id": len(tareas["tareas"]) + 1,
        "categoria": "revision",
        "prioridad": "ALTA",
        "emoji": "🔴",
        "descripcion": f"CUARENTENA: Fuente '{fuente}' bloqueada por circuit breaker",
        "detalle": f"Tasa de anomalias: {tasa:.0%}. Requiere revision humana antes de integrar.",
        "anomalias_muestra": [a.get('wp_anomalo', '') for a in anomalias_muestra],
        "estado": "pendiente",
        "fecha": datetime.now().isoformat()
    })

    with open(tareas_path, 'w', encoding='utf-8') as f:
        json.dump(tareas, f, indent=2, ensure_ascii=False)
    print(f"  Tarea de cuarentena generada en tareas_pendientes.json")

