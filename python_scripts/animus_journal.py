import time
from pathlib import Path

LOG_DIR = Path("journal")
LOG_DIR.mkdir(exist_ok=True)

def escribir_journal(entrada):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    archivo_log = LOG_DIR / f"session_{time.strftime('%Y%m%d')}.log"
    
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {entrada}\n")
    print(f"📓 Journal actualizado: {entrada[:50]}...")

# Esto lo integraremos en el Hunter para que cada hallazgo se escriba al disco al instante.