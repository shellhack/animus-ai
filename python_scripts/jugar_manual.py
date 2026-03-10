"""
Script para jugar manualmente y crear el save state correcto.

Controles:
  Flechas    → moverse
  Z          → botón A
  X          → botón B  
  Enter      → Start
  Backspace  → Select
  Escape     → Guardar state y salir

Instrucciones:
  1. Sal de la casa de Ash
  2. Camina hacia el norte hasta estar claramente en Pallet Town
  3. Presiona Escape para guardar el state y salir
"""

from pyboy import PyBoy
import sys

rom = sys.argv[1] if len(sys.argv) > 1 else "pokemon_azul.gb"
state_file = rom.replace(".gb", ".gb.state")

print("🎮 Modo manual — controla a Ash con las flechas del teclado")
print("   Z=A  X=B  Enter=Start  Escape=Guardar y salir")
print(f"   El state se guardará en: {state_file}")

pyboy = PyBoy(rom, window="SDL2")
pyboy.set_emulation_speed(1)  # velocidad normal

# Si existe state previo, cargarlo
import os
if os.path.exists(state_file):
    print(f"📂 Cargando state existente: {state_file}")
    with open(state_file, "rb") as f:
        pyboy.load_state(f)

ultima_pos = None
try:
    while True:
        if not pyboy.tick():
            break
        m = pyboy.memory[0xD35E]
        x = pyboy.memory[0xD362]
        y = pyboy.memory[0xD361]
        if (m, x, y) != ultima_pos:
            print(f"Mapa={m} X={x} Y={y}")
            ultima_pos = (m, x, y)
finally:
    # Guardar state al salir
    m = pyboy.memory[0xD35E]
    x = pyboy.memory[0xD362]
    y = pyboy.memory[0xD361]
    print(f"\n💾 Guardando state en: {state_file}")
    print(f"   Posición final: Mapa={m} X={x} Y={y}")
    with open(state_file, "wb") as f:
        pyboy.save_state(f)
    pyboy.stop()
    print("✅ Listo — corre el agente con ese state.")
