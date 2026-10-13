#!/usr/bin/env python3
"""Grava o audio do carro: o motor e a rua (com carros passando e o tique
das letras da conversa por cima), o som abaixando junto com o fade e o
refrao de "Amanda" estreando na primeira foto."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from apu import APU, gravar_wav
import robo

sym = load_labels("build/jogo-labels.txt")
B, START, RIGHT = 0x02, 0x08, 0x80
FALANTE_TAB = [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1]
nes, apu, som = NES("jogo.nes"), APU(), []

def anda(botao=0, n=1, gravando=False):
    for _ in range(n):
        nes.frame(botao)
        if gravando:
            som.extend(apu.quadro(nes.bus.apu))

anda(n=12); anda(START, 1); anda(n=70)
for _ in range(200):
    anda(RIGHT, 1)
    if nes.bus.ram[sym["perto"]]:
        break
anda(B, 1)
for _ in FALANTE_TAB:
    anda(n=400)
    anda(B, 1)
anda(n=20)
anda(B, 1)
anda(n=10)
robo.joga(nes, sym, 12000, ate=lambda n: n.bus.ram[sym["jogo_fase"]] == 1)
anda(n=60)
anda(B, 1)                                  # -> o carro

def ate_ler():
    for _ in range(400):
        anda(gravando=True)
        if nes.bus.ram[sym["dialogo"]] == 3:
            break
    anda(n=90, gravando=True)

ate_ler()                                   # a rua sozinha, ate a Amanda falar
while nes.bus.ram[sym["carro_fase"]] != 2:
    anda(B, 1, gravando=True)
    ate_ler()
anda(n=240, gravando=True)                  # mais um pouco de rua
anda(B, 1, gravando=True)                   # escurece -> primeira foto
anda(n=60 * 8, gravando=True)               # o refrao estreando

dur, pico = gravar_wav("build/carro.wav", som)
print(f"build/carro.wav  --  {dur:.1f} s, pico {pico:.3f}")
