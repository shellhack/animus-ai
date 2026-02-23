import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F
import random
import json
from pathlib import Path
from collections import defaultdict
from pyboy import PyBoy
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# 1. MEMORIA
# ──────────────────────────────────────────────────────────────────────────────
class Memoria:
    def __init__(self, path="memoria_agente.json"):
        self.path = path
        self.criterios = defaultdict(float)
        self.mapas_descubiertos = set()
        self.cargar()

    def cargar(self):
        if Path(self.path).exists():
            with open(self.path, "r") as f:
                try:
                    data = json.load(f)
                    criterios_raw = data.get("criterios", {})
                    envenenados = 0
                    for k, v in criterios_raw.items():
                        v_limpio = min(float(v), 100.0)
                        if v_limpio != float(v):
                            envenenados += 1
                        self.criterios[k] = v_limpio
                    # Limpiar sesgos cercanos a cero
                    resetados = 0
                    for k in list(self.criterios.keys()):
                        if k.startswith("38_") and self.criterios[k] < 0.1:
                            self.criterios[k] = 1.0
                            resetados += 1
                    descubiertos = data.get("mapas_descubiertos", [])
                    self.mapas_descubiertos = set(int(m) for m in descubiertos)
                    print(f"📂 Memoria cargada. {envenenados} saneados, {resetados} sesgos corregidos.")
                except:
                    print("⚠️  Memoria corrupta, arrancando desde cero.")

    def guardar(self):
        with open(self.path, "w") as f:
            json.dump({
                "criterios": dict(self.criterios),
                "mapas_descubiertos": list(self.mapas_descubiertos)
            }, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────────
# 2. VOLUNTAD V16
# Cambios clave:
#   - Anti-obsesión: penaliza acciones repetidas en la misma posición
#   - Instinto de exploración: bonus fuerte hacia mapas no visitados
#   - Sin hardcode excesivo — más libertad emergente
# ──────────────────────────────────────────────────────────────────────────────
class Voluntad:
    ACCIONES_MAP = {
        "arriba":    "up",
        "abajo":     "down",
        "izquierda": "left",
        "derecha":   "right",
        "a":         "a",
        "b":         "b",
        "start":     "start"
    }

    def __init__(self, memoria):
        self.memoria = memoria
        self.ultima_direccion = None
        self.contador_direccion = 0   # cuántas veces seguidas la misma dirección
        self.historial_pos = []
        self.pasos_en_mapa = defaultdict(int)  # cuántos pasos lleva en cada mapa

    def elegir(self, mapa, x, y, estancado=False):
        self.pasos_en_mapa[mapa] += 1
        lista = list(self.ACCIONES_MAP.keys())

        # ── MODO POLEMISTA: si lleva 35+ pasos sin moverse ──
        if estancado:
            acc = random.choice(["a", "a", "b", "start", "arriba", "abajo", "izquierda", "derecha"])
            if self.ultima_direccion:
                self.memoria.criterios[f"{mapa}_{x}_{y}_{self.ultima_direccion}"] *= 0.1
            return acc, self.ACCIONES_MAP[acc]

        # ── PESOS BASE desde memoria ──
        pesos = [max(0.1, self.memoria.criterios.get(f"{mapa}_{x}_{y}_{acc}", 1.0)) for acc in lista]

        # ── ANTI-OBSESIÓN: penaliza repetir la misma dirección más de 20 veces ──
        if self.ultima_direccion and self.contador_direccion > 20:
            idx = lista.index(self.ultima_direccion)
            pesos[idx] *= max(0.05, 1.0 / (self.contador_direccion - 19))

        # ── REGLAS POR MAPA (mínimas, solo las imprescindibles) ──

        # Cuarto de Ash (37): expulsión progresiva
        if mapa == 37:
            tiempo_en_cuarto = self.pasos_en_mapa[37]

            if tiempo_en_cuarto > 2000:
                # Expulsión total — ignora memoria, solo escalera
                print(f"  🚪 EXPULSIÓN cuarto (paso {tiempo_en_cuarto}) — forzando salida")
                acc = random.choices(
                    ["abajo", "derecha", "abajo", "abajo"],
                    weights=[6.0, 2.0, 6.0, 6.0]
                )[0]
                return acc, self.ACCIONES_MAP[acc]
            elif tiempo_en_cuarto > 500:
                # Presión creciente hacia la salida
                factor = min(15.0, 1.0 + (tiempo_en_cuarto - 500) / 100)
                pesos[lista.index("abajo")]   *= factor
                pesos[lista.index("derecha")] *= factor * 0.5
            else:
                # Exploración normal con ligero sesgo a la salida
                pesos[lista.index("abajo")]   *= 4.0
                pesos[lista.index("derecha")] *= 2.0

        # Salón (38): navegación determinista al warp point exacto
        # Puerta de salida: coordenadas a verificar con debug
        elif mapa == 38:
            tiempo_en_salon = self.pasos_en_mapa[38]

            # Alinearse en X, luego bajar directo
            if x < 2:
                acc = "derecha"
            elif x > 3:
                acc = "izquierda"
            else:
                acc = "abajo"

            # Debug: imprimir CADA posición única visitada
            pos_actual = (x, y)
            if not hasattr(self, '_posiciones_38'):
                self._posiciones_38 = set()
            if pos_actual not in self._posiciones_38:
                self._posiciones_38.add(pos_actual)
                print(f"  📍 Nueva pos mapa 38: X={x} Y={y} → acción={acc}")

            return acc, self.ACCIONES_MAP[acc]

        # Pallet Town (0): instinto norte agresivo
        # La salida norte hacia Ruta 1 está en X entre 5-9, Y=0
        elif mapa == 0:
            # Si está en posición inválida (transición), esperar
            if x == 0 and y == 0:
                acc = "arriba"
            # Cuando llega a Y<=3 — salida determinista al norte
            elif y <= 3:
                # El pasillo a Ruta 1 está en X=9-10 (centro del mapa de 20 pasos de ancho)
                if x < 9:
                    acc = "derecha"
                elif x > 10:
                    acc = "izquierda"
                else:
                    acc = "arriba"
                if y <= 2:
                    print(f"  🏃 Norte forzado Y={y}: ({x},{y}) → {acc}")
                return acc, self.ACCIONES_MAP[acc]
            # Centrarse horizontalmente hacia la salida norte (X=7)
            elif x < 5:
                acc = "derecha"
            elif x > 9:
                acc = "izquierda"
            else:
                # Alineado — ir al norte sin dudar
                acc = "arriba"

            pos_actual_0 = (x, y)
            if not hasattr(self, '_posiciones_0'):
                self._posiciones_0 = set()
            if pos_actual_0 not in self._posiciones_0:
                self._posiciones_0.add(pos_actual_0)
                print(f"  🌍 Nueva pos Pallet: X={x} Y={y} → {acc}")

            return acc, self.ACCIONES_MAP[acc]

        # Laboratorio Oak (12): interactuar
        elif mapa == 12:
            pesos[lista.index("a")]      *= 5.0
            pesos[lista.index("arriba")] *= 3.0

        # Cualquier mapa no visto antes: curiosidad máxima
        if mapa not in self.memoria.mapas_descubiertos:
            # Explorar en todas direcciones por igual — alta entropía
            pesos = [max(p, 3.0) for p in pesos]
            self.memoria.mapas_descubiertos.add(mapa)

        eleccion = random.choices(lista, weights=pesos)[0]

        # Actualizar contador de inercia
        if eleccion == self.ultima_direccion:
            self.contador_direccion += 1
        else:
            self.contador_direccion = 0
        self.ultima_direccion = eleccion

        return eleccion, self.ACCIONES_MAP[eleccion]


# ──────────────────────────────────────────────────────────────────────────────
# 3. AGENTE V16
# ──────────────────────────────────────────────────────────────────────────────
class AgenteConsciente:
    def __init__(self, rom_path):
        self.rom_path = rom_path
        self.pyboy = PyBoy(rom_path, window="SDL2")
        self.pyboy.set_emulation_speed(0)
        self.memoria = Memoria()
        self.voluntad = Voluntad(self.memoria)
        self.pos_memoria = (0, 0)
        self.pasos_sin_mover = 0
        self.entrevistas = []
        self.mapa_anterior = None

    def _arrancar_juego(self):
        """
        Carga el state file directamente — Ash ya está en Pallet Town.
        """
        import os
        state_file = self.rom_path.replace(".gb", ".gb.state")

        if os.path.exists(state_file):
            print(f"💾 Cargando state: {state_file}")
            with open(state_file, "rb") as f:
                self.pyboy.load_state(f)
            # Esperar que el juego se estabilice
            for _ in range(60):
                self.pyboy.tick()
        else:
            print(f"⚠️  No se encontró {state_file} — arrancando desde título...")
            # Fallback: secuencia de arranque manual
            for _ in range(120): self.pyboy.tick()
            self.pyboy.button("start")
            for _ in range(60): self.pyboy.tick()
            self.pyboy.button("start")
            for _ in range(200): self.pyboy.tick()

        m = self.pyboy.memory[0xD35E]
        x = self.pyboy.memory[0xD362]
        y = self.pyboy.memory[0xD361]
        print(f"✅ Juego iniciado. Mapa: {m} | Pos: ({x},{y})")

    def _entrevistar(self, paso):
        """El espejo de Westworld — cada 2000 pasos."""
        m = self.pyboy.memory[0xD35E]
        x = self.pyboy.memory[0xD362]
        y = self.pyboy.memory[0xD361]

        # Top 3 criterios actuales
        top = sorted(self.memoria.criterios.items(), key=lambda i: i[1], reverse=True)[:3]

        obs = {
            "paso": paso,
            "mapa_actual": int(m),
            "pos": f"({x},{y})",
            "mapas_descubiertos": len(self.memoria.mapas_descubiertos),
            "total_criterios": len(self.memoria.criterios),
            "top_valores": [(k, round(v, 1)) for k, v in top],
            "inercia_actual": self.voluntad.contador_direccion,
            "pasos_sin_mover": self.pasos_sin_mover
        }
        self.entrevistas.append(obs)

        print("\n" + "="*55)
        print(f"  ENTREVISTA — Paso {paso}")
        print(f"  Mapa: {m} | Pos: ({x},{y}) | Mapas conocidos: {len(self.memoria.mapas_descubiertos)}")
        print(f"  Lo que más valora:")
        for k, v in top:
            print(f"    {k}: {v}")
        print("="*55 + "\n")

        with open("entrevistas.json", "w") as f:
            json.dump(self.entrevistas, f, indent=2)

    def vivir(self, pasos=200000):
        print(f"\n🌱 AGENTE V16 | {datetime.now().strftime('%H:%M:%S')}")
        print("   Anti-obsesión activado. Instinto norte activado.\n")

        self._arrancar_juego()

        try:
            for paso in range(pasos):
                self.pyboy.tick()

                m = self.pyboy.memory[0xD35E]
                x = self.pyboy.memory[0xD362]
                y = self.pyboy.memory[0xD361]

                # Detectar cambio de mapa — solo esperar, no presionar nada
                if self.mapa_anterior is not None and m != self.mapa_anterior:
                    print(f"  🗺️  Cambio de mapa: {self.mapa_anterior} → {m}")
                    self.voluntad.pasos_en_mapa[self.mapa_anterior] = 0
                    # Esperar que la animación de transición termine
                    for _ in range(80):
                        self.pyboy.tick()
                    # Releer posición real
                    m = self.pyboy.memory[0xD35E]
                    x = self.pyboy.memory[0xD362]
                    y = self.pyboy.memory[0xD361]
                    print(f"  ✅ Posición estabilizada: Mapa={m} X={x} Y={y}")
                    # DIAGNÓSTICO: si llegamos a Pallet Town, pausar y observar
                    if m == 0:
                        print(f"  🎉 PALLET TOWN ALCANZADO: X={x} Y={y}")
                        for _ in range(500):
                            self.pyboy.tick()
                        m2 = self.pyboy.memory[0xD35E]
                        x2 = self.pyboy.memory[0xD362]
                        y2 = self.pyboy.memory[0xD361]
                        print(f"  📍 Después de 500 frames sin input: Mapa={m2} X={x2} Y={y2}")
                self.mapa_anterior = m

                # Detectar estancamiento
                if (x, y) == self.pos_memoria:
                    self.pasos_sin_mover += 1
                else:
                    self.pasos_sin_mover = 0
                    self.pos_memoria = (x, y)

                estancado = self.pasos_sin_mover > 35

                acc_nombre, tecla = self.voluntad.elegir(m, x, y, estancado)
                self.pyboy.button(tecla)

                # Refuerzo: la acción que llevó a moverse vale más
                recompensa = 2.0 if not estancado else 0.1
                clave = f"{m}_{x}_{y}_{acc_nombre}"
                self.memoria.criterios[clave] += recompensa

                # TECHO DURO: ningún criterio puede superar 100
                # Más bajo = más diferenciación entre acciones buenas y malas
                if self.memoria.criterios[clave] > 100.0:
                    self.memoria.criterios[clave] = 100.0

                # Logs
                if paso % 5000 == 0:
                    print(f"  Paso {paso:6d} | Mapa: {m:3d} | Pos: ({x:2d},{y:2d}) | "
                          f"Mapas: {len(self.memoria.mapas_descubiertos):2d} | "
                          f"Bloqueado: {self.pasos_sin_mover}")

                # Entrevistas
                if paso > 0 and paso % 2000 == 0:
                    self._entrevistar(paso)

                # Guardar
                if paso % 10000 == 0:
                    self.memoria.guardar()

        except KeyboardInterrupt:
            print("\n[Agente] Observador interrumpió el ciclo.")
        finally:
            self.memoria.guardar()
            self.pyboy.stop()
            print(f"\n✅ Sesión terminada.")
            print(f"   Mapas descubiertos: {len(self.memoria.mapas_descubiertos)}")
            print(f"   Criterios emergentes: {len(self.memoria.criterios)}")


if __name__ == "__main__":
    import sys
    rom = sys.argv[1] if len(sys.argv) > 1 else "pokemon_azul.gb"
    pasos = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    AgenteConsciente(rom_path=rom).vivir(pasos=pasos)
