#!/usr/bin/env python3
"""
ANIMUS Instance Generator — Fase 1
Genera instancias especializadas desde memoria_business.json existente.
Uso: python generar_instancia.py --dominio fin|gov|tech|all
"""

import json
import argparse
import os
from collections import defaultdict

# ── Definición de dominios ──────────────────────────────────────────────────
DOMINIOS = {
    "fin": {
        "nombre": "ANIMUS-FIN",
        "descripcion": "Especializado en riesgo financiero, regulación y crisis económica",
        "tokens_destino": ["regulation", "regulaci", "policy", "politi", "prevention", "prevenci", "framework", "arquitectura"],
        "tokens_origen": ["failure", "fracaso", "crisis", "bankruptcy", "colapso", "deficit", "debt", "deuda", "loss", "shortage"],
        "fuentes_web_extra": [
            "https://en.wikipedia.org/wiki/Financial_regulation",
            "https://en.wikipedia.org/wiki/Bank_run",
            "https://en.wikipedia.org/wiki/Systemic_risk",
            "https://en.wikipedia.org/wiki/Central_bank",
            "https://en.wikipedia.org/wiki/Monetary_policy",
        ]
    },
    "gov": {
        "nombre": "ANIMUS-GOV",
        "descripcion": "Especializado en corrupción institucional, reforma y política pública",
        "tokens_destino": ["reform", "reforma", "cooperation", "cooperaci", "agreement", "acuerdo", "education", "educaci"],
        "tokens_origen": ["corruption", "corrupci", "fraud", "fraude", "inequality", "desigualdad", "poverty", "pobreza"],
        "fuentes_web_extra": [
            "https://en.wikipedia.org/wiki/Political_corruption",
            "https://en.wikipedia.org/wiki/Institutional_reform",
            "https://en.wikipedia.org/wiki/Good_governance",
            "https://en.wikipedia.org/wiki/Rule_of_law",
            "https://en.wikipedia.org/wiki/Public_policy",
        ]
    },
    "tech": {
        "nombre": "ANIMUS-TECH",
        "descripcion": "Especializado en brechas tecnológicas, algoritmos e innovación",
        "tokens_destino": ["algorithm", "algoritmo", "innovation", "innovaci", "discovered", "descubrimiento", "solution", "acuerdo"],
        "tokens_origen": ["gap", "brecha", "failure", "fracaso", "crisis", "inequality", "desigualdad"],
        "fuentes_web_extra": [
            "https://en.wikipedia.org/wiki/Digital_divide",
            "https://en.wikipedia.org/wiki/Algorithmic_bias",
            "https://en.wikipedia.org/wiki/Disruptive_innovation",
            "https://en.wikipedia.org/wiki/Technology_gap",
            "https://en.wikipedia.org/wiki/Artificial_intelligence",
        ]
    }
}

def cargar_memoria(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def filtrar_conexiones(conexiones: dict, dominio: dict) -> dict:
    """Filtra conexiones relevantes para el dominio dado."""
    tokens_d = dominio["tokens_destino"]
    tokens_o = dominio["tokens_origen"]
    
    filtradas = {}
    for clave, peso in conexiones.items():
        if "__>" not in clave:
            continue
        partes = clave.split("__>")
        if len(partes) != 2:
            continue
        origen, destino = partes
        
        # Incluir si el destino o el origen matchea el dominio
        match_destino = any(t in destino.lower() for t in tokens_d)
        match_origen = any(t in origen.lower() for t in tokens_o)
        
        if match_destino or match_origen:
            filtradas[clave] = peso
    
    return filtradas

def calcular_estadisticas(conexiones: dict) -> dict:
    """Calcula estadísticas del corpus filtrado."""
    if not conexiones:
        return {}
    
    # Agrupar por patrón token_origen → token_destino
    patrones = defaultdict(lambda: {"fuentes": set(), "fuerza": 0.0})
    
    for clave, peso in conexiones.items():
        partes = clave.split("__>")
        if len(partes) != 2:
            continue
        tok_o = partes[0].split("_")[-1]
        tok_d = partes[1].split("_")[-1]
        key = f"{tok_o}→{tok_d}"
        
        # Extraer nombre de fuente
        fuente = partes[0].split("_")[0] if "_" in partes[0] else partes[0][:10]
        patrones[key]["fuentes"].add(fuente)
        patrones[key]["fuerza"] += peso
    
    # Top patrones
    top = sorted(
        [(k, len(v["fuentes"]), v["fuerza"]) for k, v in patrones.items()],
        key=lambda x: x[2],
        reverse=True
    )[:10]
    
    return {
        "total_conexiones": len(conexiones),
        "total_patrones": len(patrones),
        "top_patrones": [{"patron": p, "fuentes": f, "fuerza": round(s, 1)} for p, f, s in top]
    }

def generar_instancia(memoria_path: str, dominio_key: str, output_dir: str):
    """Genera una instancia especializada de ANIMUS."""
    
    if dominio_key not in DOMINIOS and dominio_key != "all":
        print(f"❌ Dominio '{dominio_key}' no reconocido. Usa: {', '.join(DOMINIOS.keys())}, all")
        return
    
    dominios_a_generar = DOMINIOS if dominio_key == "all" else {dominio_key: DOMINIOS[dominio_key]}
    
    print(f"📂 Cargando memoria desde: {memoria_path}")
    memoria = cargar_memoria(memoria_path)
    conexiones_totales = len(memoria.get("conexiones", {}))
    print(f"✅ {conexiones_totales} conexiones cargadas\n")
    
    for key, dominio in dominios_a_generar.items():
        nombre = dominio["nombre"]
        print(f"🧬 Generando {nombre}...")
        print(f"   📋 {dominio['descripcion']}")
        
        # Filtrar conexiones para este dominio
        conexiones_filtradas = filtrar_conexiones(memoria.get("conexiones", {}), dominio)
        stats = calcular_estadisticas(conexiones_filtradas)
        
        print(f"   🔗 Conexiones filtradas: {stats.get('total_conexiones', 0)} / {conexiones_totales} ({stats.get('total_conexiones', 0)*100//conexiones_totales}%)")
        print(f"   🧠 Patrones únicos: {stats.get('total_patrones', 0)}")
        
        if stats.get("top_patrones"):
            print(f"   🏆 Top patrón: {stats['top_patrones'][0]['patron']} ({stats['top_patrones'][0]['fuentes']} fuentes, fuerza {stats['top_patrones'][0]['fuerza']})")
        
        # Construir memoria especializada
        memoria_instancia = {
            "conexiones": conexiones_filtradas,
            "lenguaje": memoria.get("lenguaje", {}),
            "metadata": {
                "instancia": nombre,
                "descripcion": dominio["descripcion"],
                "generado_desde": "memoria_business.json",
                "conexiones_heredadas": stats.get("total_conexiones", 0),
                "conexiones_padre": conexiones_totales,
                "top_patrones": stats.get("top_patrones", []),
                "fuentes_web_recomendadas": dominio["fuentes_web_extra"]
            }
        }
        
        # Guardar archivo
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"memoria_{nombre.lower().replace('-', '_')}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(memoria_instancia, f, ensure_ascii=False, indent=2)
        
        print(f"   💾 Guardado: {output_path}")
        
        # Generar reporte de nacimiento
        reporte_path = os.path.join(output_dir, f"nacimiento_{nombre.lower().replace('-', '_')}.md")
        with open(reporte_path, 'w', encoding='utf-8') as f:
            f.write(f"# Nacimiento de {nombre}\n\n")
            f.write(f"**Generado:** desde ANIMUS principal (memoria_business.json)\n")
            f.write(f"**Especialización:** {dominio['descripcion']}\n\n")
            f.write(f"## Herencia\n\n")
            f.write(f"- Conexiones heredadas: {stats.get('total_conexiones', 0)} de {conexiones_totales} ({stats.get('total_conexiones', 0)*100//conexiones_totales}%)\n")
            f.write(f"- Patrones únicos: {stats.get('total_patrones', 0)}\n\n")
            f.write(f"## Top Patrones\n\n")
            f.write(f"| Patrón | Fuentes | Fuerza |\n")
            f.write(f"|--------|---------|--------|\n")
            for p in stats.get("top_patrones", []):
                f.write(f"| {p['patron']} | {p['fuentes']} | {p['fuerza']} |\n")
            f.write(f"\n## Fuentes Web Recomendadas\n\n")
            for url in dominio["fuentes_web_extra"]:
                f.write(f"- {url}\n")
            f.write(f"\n## Nota Filosófica\n\n")
            f.write(f"Esta instancia no fue programada desde cero — emergió por filtrado natural\n")
            f.write(f"de los patrones que el sistema padre encontró sin instrucción explícita.\n")
            f.write(f"Hereda la arquitectura DAG, el decay biológico, el Protocolo Bernard,\n")
            f.write(f"y el tf-idf semántico. Solo su corpus de sabiduría es distinto.\n")
        
        print(f"   📄 Reporte: {reporte_path}\n")
    
    print("✅ Generación completa.")
    print(f"\nPara usar una instancia, copia su archivo memoria_*.json como")
    print(f"'memoria_business.json' en el directorio del proyecto hijo.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Instance Generator")
    parser.add_argument("--memoria", default="memoria_business.json", help="Path al memoria_business.json padre")
    parser.add_argument("--dominio", default="all", help="Dominio a generar: fin, gov, tech, all")
    parser.add_argument("--output", default="instancias", help="Directorio de salida")
    args = parser.parse_args()
    
    generar_instancia(args.memoria, args.dominio, args.output)
