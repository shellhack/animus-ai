from pathlib import Path

def recuperar_consciencia():
    log_dir = Path("journal")
    logs = sorted(log_dir.glob("*.log"))
    
    if not logs:
        print("📭 No hay rastro de sesiones previas.")
        return

    ultimo_log = logs[-1]
    with open(ultimo_log, "r", encoding="utf-8") as f:
        lineas = f.readlines()
        if lineas:
            ultima_linea = lineas[-1].strip()
            print(f"🧠 RECUPERACIÓN: Reanudando desde el último pensamiento:")
            print(f"   > {ultima_linea}")
            return ultima_linea

if __name__ == "__main__":
    recuperar_consciencia()