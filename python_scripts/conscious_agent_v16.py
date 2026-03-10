import numpy as np
import random
import json
import math
from pathlib import Path
from collections import defaultdict
from pyboy import PyBoy
from datetime import datetime

# 1. MEMORIA (Saneada según D21)
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
                    for k, v in criterios_raw.items():
                        # Eliminamos techos duros para permitir fluidez 
                        self.criterios[k] = float(v)
                    descubiertos = data.get("mapas_descubiertos", [])
                    self.mapas_descubiertos = set(int(m) for m in descubiertos)
                    print(f"📂 Memoria cargada. Nodos activos: {len(self.criterios)}")
                except:
                    print("⚠️ Memoria corrupta, iniciando secuencia limpia.")

    def guardar(self):
        with open(self.path, "w") as f:
            json.dump({
                "criterios": dict(self.criterios),
                "mapas_descubiertos": list(self.mapas_descubiertos)
            }, f, indent=2)

# 2. VOLUNTAD (Implementación D05 y D21)
class Voluntad:
    ACCIONES_MAP = {"arriba": "up", "abajo": "down", "izquierda": "left", "derecha": "right", "a": "a", "b": "b", "start": "start"}

    def __init__(self, memoria):
        self.memoria = memoria
        self.ultima_direccion = None
        self.pasos_en_mapa = defaultdict(int)
        self.epsilon = 0.2

    def recalibrar_decision(self, clave, valor_actual):
        # D05: Incremento logarítmico para evitar rigidez 
        incremento = 2.0 / (1.0 + math.log(1 + valor_actual))
        self.memoria.criterios[clave] += incremento
        
        # D21: Si hay obsesión (>80), forzamos exploración 
        if self.memoria.criterios[clave] > 80.0:
            self.epsilon = max(self.epsilon, 0.5)

    def elegir(self, mapa, x, y, estancado=False):
        self.pasos_en_mapa[mapa] += 1
        lista = list(self.ACCIONES_MAP.keys())

        # --- RUPTURA DE BUCLE D23 (Optimizado para Diálogos) ---
        if estancado:
            # Animús ahora entiende que en el estancamiento, A y B son la prioridad
            # 80% de probabilidad de presionar A o B para avanzar textos
            if random.random() < 0.8:
                acc = random.choice(["a", "b"])
            else:
                acc = random.choice(lista)
            
            # Solo imprimimos cada cierto tiempo para no saturar la consola
            if self.pasos_en_mapa[mapa] % 100 == 0:
                print(f"⚠️ [D23] Diálogo detectado en mapa {mapa}. Forzando avance A/B.")
            
            return acc, self.ACCIONES_MAP[acc]

        # PRESIÓN DE SALIDA (Ajuste estructural para Mapa 37)
        pesos = [max(0.1, self.memoria.criterios.get(f"{mapa}_{x}_{y}_{acc}", 1.0)) for acc in lista]
        if mapa == 37:
            factor = 15.0 if self.pasos_en_mapa[37] > 300 else 4.0
            pesos[lista.index("abajo")] *= factor
            pesos[lista.index("derecha")] *= factor * 0.5

        # Decisión Epsilon-Greedy
        if random.random() < self.epsilon:
            acc = random.choice(lista)
            self.epsilon = max(0.1, self.epsilon * 0.98)
        else:
            acc = random.choices(lista, weights=pesos)[0]
        
        return acc, self.ACCIONES_MAP[acc]

# 3. AGENTE (Protocolo de Prioridad)
class AgenteConsciente:
    def __init__(self, rom_path):
        self.rom_path = rom_path
        self.pyboy = PyBoy(rom_path, window="SDL2")
        self.pyboy.set_emulation_speed(0)
        self.memoria = Memoria()
        self.voluntad = Voluntad(self.memoria)
        self.pos_mem = (0, 0)
        self.bloqueo = 0

    def vivir(self, pasos=200000):
        print(f"🌱 AGENTE V16 + D23 | INICIO: {datetime.now()}")
        # Carga de estado omitida para brevedad, asumiendo inicio limpio
        
        try:
            for p in range(pasos):
                self.pyboy.tick()
                m, x, y = self.pyboy.memory[0xD35E], self.pyboy.memory[0xD362], self.pyboy.memory[0xD361]

                # INTERRUPCIÓN DE COMBATE (Prioridad Tanenbaum)
                if self.pyboy.memory[0xD057] != 0:
                    self.pyboy.button("a")
                    continue

                # DETECCIÓN DE RIGIDEZ
                if (x, y) == self.pos_mem: 
                    self.bloqueo += 1
                else: 
                    self.bloqueo, self.pos_mem = 0, (x, y)

                # --- LÓGICA DE PULSACIÓN HUMANA (D23) ---
                if self.bloqueo > 15:
                    # Reducimos la velocidad a cada 30 pasos para que el juego respire
                    if p % 30 == 0:
                        acc_n, tecla = self.voluntad.elegir(m, x, y, True)
                        self.pyboy.button(tecla)
                        # Opcional: print para ver qué botón está intentando
                        # print(f"  [D23] Intentando {acc_n} para cerrar letrero...")
                else:
                    acc_n, tecla = self.voluntad.elegir(m, x, y, False)
                    self.pyboy.button(tecla)

                # RECALIBRACIÓN LOGARÍTMICA
                self.voluntad.recalibrar_decision(f"{m}_{x}_{y}_{acc_n}", self.memoria.criterios[f"{m}_{x}_{y}_{acc_n}"])

                if p % 10000 == 0: self.memoria.guardar()
        finally:
            self.memoria.guardar()
            self.pyboy.stop()

if __name__ == "__main__":
    AgenteConsciente("pokemon_azul.gb").vivir()