import json

MEMORIA_FILE = "memoria_business.json"

def podar_hipertrofia():
    with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
        memoria = json.load(f)

    # Buscamos el peso total acumulado del token 'algoritmo'
    # Sumamos su presencia en todas las soluciones
    peso_algoritmo = sum(v for k, v in memoria["soluciones"].items() if k.endswith("_algorithm"))
    
    print(f"📊 Peso actual de 'algoritmo': {peso_algoritmo}")

    if peso_algoritmo > 10000:
        print("⚠️ HIPERTROFIA DETECTADA. Iniciando poda sistémica...")
        
        # Restamos el exceso (500 puntos)
        puntos_a_repartir = 500
        factor_reduccion = (peso_algoritmo - puntos_a_repartir) / peso_algoritmo
        
        for k in memoria["soluciones"]:
            if k.endswith("_algorithm"):
                memoria["soluciones"][k] *= factor_reduccion
        
        # Inyectamos el peso en la 'sombra' (vulnerability y corruption)
        # Esto crea equilibrio artificial pero necesario
        memoria["problemas"]["mutacion_vulnerability"] = memoria["problemas"].get("mutacion_vulnerability", 0) + 250
        memoria["problemas"]["mutacion_corruption"] = memoria["problemas"].get("mutacion_corruption", 0) + 250
        
        with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(memoria, f, indent=2, ensure_ascii=False)
        
        print("✅ Rebalanceo completado. ANIMUS es ahora un 5% más escéptico.")
    else:
        print("✅ Sistema estable. No se requiere poda.")

if __name__ == "__main__":
    podar_hipertrofia()