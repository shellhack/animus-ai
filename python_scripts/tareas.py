# -*- coding: utf-8 -*-
"""
ANIMUS — Modulo de Tareas
ANIMUS genera tareas concretas para Ernesto cuando detecta
brechas que no puede resolver solo.

Uso:
    python tareas.py              # Ver tareas pendientes
    python tareas.py --generar    # ANIMUS genera nuevas tareas desde su introspección
    python tareas.py --completar 3  # Marcar tarea #3 como completada
    python tareas.py --agregar    # Agregar tarea manualmente
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORIA_PATH = Path(__file__).parent / "memoria_business.json"
TAREAS_PATH  = Path(__file__).parent / "tareas_pendientes.json"

# ── Categorías de tareas ──────────────────────────────────────────────────────

CATEGORIAS = {
    "libro":     "📚 Conseguir libro",
    "fuente":    "🌐 Agregar fuente",
    "api":       "🔌 Conectar API",
    "publicar":  "📢 Publicar contenido",
    "archivo":   "📁 Gestión de archivos",
    "revision":  "🔍 Revisión humana",
    "otro":      "💡 Otro",
}

# ── Libros que ANIMUS puede pedir según sus brechas ───────────────────────────

LIBROS_POR_BRECHA = {
    "neural":       [
        ("Deep Learning", "Goodfellow, Bengio, Courville", "Redes neuronales profundas — refuerza token 'neural'"),
        ("The Brain That Changes Itself", "Norman Doidge", "Neuroplasticidad — patron fracaso → adaptacion"),
    ],
    "discovered":   [
        ("The Structure of Scientific Revolutions", "Thomas Kuhn", "Ya procesado"),
        ("Surely You're Joking Mr Feynman", "Richard Feynman", "Descubrimiento cientifico desde adentro"),
        ("The Demon-Haunted World", "Carl Sagan", "Pensamiento critico y descubrimiento"),
    ],
    "algorithm":    [
        ("Algorithms to Live By", "Brian Christian & Griffiths", "Algoritmos en decisiones humanas"),
        ("The Art of Problem Solving", "Rusczyk", "Resolucion sistematica de problemas"),
    ],
    "framework":    [
        ("Clean Architecture", "Robert C. Martin", "Arquitectura de software — patron limitacion → arquitectura"),
        ("Thinking in Systems", "Donella Meadows", "Sistemas complejos y sus estructuras"),
    ],
    "education":    [
        ("Make It Stick", "Brown, Roediger, McDaniel", "Ciencia del aprendizaje efectivo"),
        ("A Mind for Numbers", "Barbara Oakley", "Como aprender cosas dificiles"),
    ],
    "cooperation":  [
        ("The Evolution of Cooperation", "Robert Axelrod", "Cooperacion emergente — conecta con Dawkins"),
        ("Nonviolent Communication", "Marshall Rosenberg", "Comunicacion y cooperacion"),
    ],
    "developed":    [
        ("Sapiens", "Yuval Noah Harari", "Historia del desarrollo humano — muy denso en patrones"),
        ("Guns Germs and Steel", "Jared Diamond", "Por que unas civilizaciones se desarrollan mas"),
    ],
    "innovation":   [
        ("The Innovator's Dilemma", "Clayton Christensen", "Como la innovacion surge del fracaso"),
        ("Zero to One", "Peter Thiel", "Innovacion radical vs incremental"),
    ],
}

FUENTES_POR_BRECHA = {
    "latinoamerica": [
        ("https://cepal.org/es/notas", "CEPAL — economia latinoamericana"),
        ("https://listindiario.com/economia", "Listin Diario — RD economia"),
        ("https://eldinero.com.do", "El Dinero — finanzas RD"),
    ],
    "filosofia": [
        ("https://plato.stanford.edu/entries/consciousness", "SEP — consciencia"),
        ("https://plato.stanford.edu/entries/artificial-intelligence", "SEP — IA y mente"),
    ],
    "ciencia": [
        ("https://quantamagazine.org/computer-science", "Quanta — matematicas y computacion"),
        ("https://nature.com/subjects/artificial-intelligence", "Nature — IA investigacion"),
    ],
}


# ── Core functions ────────────────────────────────────────────────────────────

def cargar_tareas():
    if TAREAS_PATH.exists():
        with open(TAREAS_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {"tareas": [], "completadas": [], "ultimo_analisis": None}

def guardar_tareas(data):
    with open(TAREAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def cargar_memoria():
    with open(MEMORIA_PATH, encoding='utf-8') as f:
        return json.load(f)

def siguiente_id(data):
    todas = data["tareas"] + data["completadas"]
    if not todas:
        return 1
    return max(t["id"] for t in todas) + 1


# ── ANIMUS analysis engine ────────────────────────────────────────────────────

def analizar_brechas(mem):
    """ANIMUS examines its own memory and identifies gaps."""
    conexiones = mem["conexiones"]
    lenguaje   = mem["lenguaje"]

    # Tokens covered
    todos_tokens = set()
    for k in conexiones:
        p = k.split("__>")
        if len(p) == 2:
            todos_tokens.add(p[0].split("_")[-1])
            todos_tokens.add(p[1].split("_")[-1])

    TODOS_TOKENS_CONOCIDOS = {
        "failure", "gap", "crisis", "collapse", "limitation", "shortage",
        "bottleneck", "vulnerability", "inequality", "poverty", "corruption",
        "fraud", "burnout", "algorithm", "neural", "education", "training",
        "innovation", "solution", "regulation", "cooperation", "developed",
        "discovered", "transformed", "framework", "automation", "prevention",
        "reform", "incentive", "renewable", "loss", "threat", "disruption",
    }

    sin_cobertura = TODOS_TOKENS_CONOCIDOS - todos_tokens

    # Weak tokens (few connections)
    fuerza_token = defaultdict(float)
    for k, v in conexiones.items():
        p = k.split("__>")
        if len(p) == 2:
            fuerza_token[p[0].split("_")[-1]] += v
            fuerza_token[p[1].split("_")[-1]] += v

    debiles = [t for t, f in fuerza_token.items() if f < 20 and t in TODOS_TOKENS_CONOCIDOS]

    # Source diversity
    fuentes_actuales = set()
    for k in conexiones:
        fuentes_actuales.add(k.split("_")[0])

    return {
        "sin_cobertura": list(sin_cobertura),
        "tokens_debiles": debiles,
        "n_conexiones": len(conexiones),
        "n_vocabulario": len(lenguaje),
        "n_fuentes": len(fuentes_actuales),
    }


def generar_tareas_desde_brechas(mem, data):
    """ANIMUS generates specific tasks based on its gaps."""
    brechas = analizar_brechas(mem)
    nuevas  = []
    fecha   = datetime.now().isoformat()

    # 1. Books for weak tokens
    for token in brechas["tokens_debiles"][:3]:
        if token in LIBROS_POR_BRECHA:
            for titulo, autor, razon in LIBROS_POR_BRECHA[token][:1]:
                if titulo == "Ya procesado":
                    continue
                # Check not already requested
                ya_pedido = any(
                    t.get("titulo") == titulo
                    for t in data["tareas"] + data["completadas"]
                )
                if not ya_pedido:
                    nuevas.append({
                        "id": siguiente_id(data) + len(nuevas),
                        "categoria": "libro",
                        "prioridad": "ALTA",
                        "titulo": titulo,
                        "descripcion": f"Conseguir PDF de '{titulo}' ({autor})",
                        "razon": f"Token '{token}' debil en mi memoria. {razon}",
                        "impacto": f"Reforzaria patron {token} → solucion con nueva fuente independiente",
                        "comando": f"python process_book_v2.py \"{titulo}.pdf\" memoria_business.json --tipo wisdom --nombre {token}_book",
                        "fecha_generada": fecha,
                        "estado": "pendiente",
                    })

    # 2. Books for uncovered tokens
    for token in brechas["sin_cobertura"][:2]:
        if token in LIBROS_POR_BRECHA:
            for titulo, autor, razon in LIBROS_POR_BRECHA[token][:1]:
                if titulo == "Ya procesado":
                    continue
                ya_pedido = any(
                    t.get("titulo") == titulo
                    for t in data["tareas"] + data["completadas"]
                )
                if not ya_pedido:
                    nuevas.append({
                        "id": siguiente_id(data) + len(nuevas),
                        "categoria": "libro",
                        "prioridad": "MEDIA",
                        "titulo": titulo,
                        "descripcion": f"Conseguir PDF de '{titulo}' ({autor})",
                        "razon": f"Token '{token}' sin cobertura en mi memoria. {razon}",
                        "impacto": f"Abriria nuevo dominio de conocimiento: {token}",
                        "comando": f"python process_book_v2.py \"{titulo}.pdf\" memoria_business.json --tipo wisdom --nombre {token}_new",
                        "fecha_generada": fecha,
                        "estado": "pendiente",
                    })

    # 3. Autonomous self-portrait — can be regenerated periodically
    nuevas.append({
        "id": siguiente_id(data) + len(nuevas),
        "categoria": "archivo",
        "prioridad": "RUTINA",
        "titulo": "Regenerar autorretrato",
        "descripcion": "Regenerar autorretrato_filosofico.txt con el estado actual de memoria",
        "razon": "El autorretrato debe actualizarse cada mes para reflejar el crecimiento",
        "impacto": "ANIMUS se lee a si mismo con conocimiento actualizado — strange loop continuo",
        "comando": "python generar_autorretrato.py && python process_book_v2.py autorretrato_filosofico.txt memoria_business.json --tipo wisdom --nombre animus_self",
        "fecha_generada": fecha,
        "estado": "pendiente",
    })

    # 4. Substack publication
    n_conn = brechas["n_conexiones"]
    if n_conn >= 1000:
        nuevas.append({
            "id": siguiente_id(data) + len(nuevas),
            "categoria": "publicar",
            "prioridad": "ALTA",
            "titulo": "Publicar reporte en Substack",
            "descripcion": "Publicar ANIMUS_Autoconciencia.pdf como articulo en Substack o LinkedIn",
            "razon": f"Con {n_conn} conexiones y 36 convergencias documentadas, el proyecto tiene valor academico y comercial",
            "impacto": "Visibilidad del proyecto — potenciales clientes, colaboradores, o reconocimiento academico",
            "comando": "Abrir Substack, crear articulo, pegar contenido del PDF de autoconciencia",
            "fecha_generada": fecha,
            "estado": "pendiente",
        })

    # 5. API connections
    nuevas.append({
        "id": siguiente_id(data) + len(nuevas),
        "categoria": "api",
        "prioridad": "MEDIA",
        "titulo": "Conectar API de noticias RD",
        "descripcion": "Buscar API gratuita de noticias dominicanas (Listin, Diario Libre) para entrenamiento automatico",
        "razon": "Las fuentes latinoamericanas activan vocabulario espanol nativo mejor que las traducciones",
        "impacto": "Vocabulario espanol creceria mas rapido — actualmente en 309 palabras, objetivo 500+",
        "comando": "Buscar en rapidapi.com APIs de noticias latinoamericanas, agregar URL a corpus_dinamico.json",
        "fecha_generada": fecha,
        "estado": "pendiente",
    })

    return nuevas


# ── Display ───────────────────────────────────────────────────────────────────

def mostrar_tareas(data):
    pendientes = [t for t in data["tareas"] if t["estado"] == "pendiente"]
    completadas = data["completadas"]

    print("\n" + "=" * 65)
    print("  ANIMUS — TAREAS PARA ERNESTO")
    print(f"  {datetime.now().strftime('%d de %B de %Y')}")
    print("=" * 65)

    if not pendientes:
        print("\n  No hay tareas pendientes.\n")
        print("  Corre: python tareas.py --generar")
        print("  Para que ANIMUS analice sus brechas y genere nuevas tareas.\n")
        return

    # Group by priority
    for prioridad, emoji in [("ALTA", "🔴"), ("MEDIA", "🟡"), ("RUTINA", "🟢")]:
        grupo = [t for t in pendientes if t.get("prioridad") == prioridad]
        if not grupo:
            continue
        print(f"\n  {emoji} PRIORIDAD {prioridad}")
        print("  " + "─" * 50)
        for t in grupo:
            cat = CATEGORIAS.get(t["categoria"], t["categoria"])
            print(f"\n  [{t['id']}] {cat}: {t['titulo']}")
            print(f"       {t['descripcion']}")
            print(f"       Por qué: {t['razon'][:80]}...")
            print(f"       Impacto: {t['impacto'][:80]}...")
            if t.get("comando"):
                print(f"       Comando: {t['comando'][:70]}...")

    print(f"\n  Total pendientes: {len(pendientes)}")
    print(f"  Completadas: {len(completadas)}")
    print()
    print("  Comandos:")
    print("  python tareas.py --completar <id>   # Marcar como completada")
    print("  python tareas.py --generar          # Generar nuevas tareas")
    print()


def completar_tarea(data, tarea_id):
    for i, t in enumerate(data["tareas"]):
        if t["id"] == tarea_id:
            t["estado"] = "completada"
            t["fecha_completada"] = datetime.now().isoformat()
            data["completadas"].append(t)
            data["tareas"].pop(i)
            guardar_tareas(data)
            print(f"\n  Tarea #{tarea_id} marcada como completada.")
            print(f"  '{t['titulo']}'\n")
            return
    print(f"\n  Tarea #{tarea_id} no encontrada.\n")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANIMUS Task Manager")
    parser.add_argument("--generar",    action="store_true",
                        help="ANIMUS genera tareas desde sus brechas")
    parser.add_argument("--completar",  type=int, default=None,
                        help="Marcar tarea como completada por ID")
    parser.add_argument("--agregar",    action="store_true",
                        help="Agregar tarea manualmente")
    args = parser.parse_args()

    data = cargar_tareas()

    if args.completar:
        completar_tarea(data, args.completar)

    elif args.generar:
        if not MEMORIA_PATH.exists():
            print("ERROR: memoria_business.json no encontrado")
            sys.exit(1)

        mem = cargar_memoria()
        print("\n  ANIMUS analizando sus brechas...")

        nuevas = generar_tareas_desde_brechas(mem, data)
        data["tareas"].extend(nuevas)
        data["ultimo_analisis"] = datetime.now().isoformat()
        guardar_tareas(data)

        print(f"  {len(nuevas)} tareas nuevas generadas.\n")
        mostrar_tareas(data)

    elif args.agregar:
        print("\n  Agregar tarea manual:")
        titulo = input("  Titulo: ").strip()
        desc   = input("  Descripcion: ").strip()
        cat    = input("  Categoria (libro/fuente/api/publicar/archivo/otro): ").strip()
        prio   = input("  Prioridad (ALTA/MEDIA/RUTINA): ").strip().upper()
        nueva = {
            "id": siguiente_id(data),
            "categoria": cat or "otro",
            "prioridad": prio or "MEDIA",
            "titulo": titulo,
            "descripcion": desc,
            "razon": "Agregada manualmente",
            "impacto": "Por definir",
            "comando": "",
            "fecha_generada": datetime.now().isoformat(),
            "estado": "pendiente",
        }
        data["tareas"].append(nueva)
        guardar_tareas(data)
        print(f"\n  Tarea #{nueva['id']} agregada.\n")

    else:
        mostrar_tareas(data)
