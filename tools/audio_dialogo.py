#!/usr/bin/env python3
"""Grava o audio da cena de fala: musica + o tique das letras."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from apu import APU, gravar_wav

sym = load_labels("build/jogo-labels.txt")
B, START, RIGHT = 0x02, 0x08, 0x80
nes, apu, som = NES("jogo.nes"), APU(), []

def anda(botao=0, n=1, gravando=False):
    for _ in range(n):
        nes.frame(botao)
        if gravando:
            som.extend(apu.quadro(nes.bus.apu))

anda(n=12); anda(START, 1); anda(n=6)
for _ in range(200):
    anda(RIGHT, 1)
    if nes.bus.ram[sym["perto"]]:
        break
anda(n=30, gravando=True)          # um instante antes de falar
anda(B, 1, gravando=True)
anda(n=300, gravando=True)         # a fala inteira
dur, pico = gravar_wav("build/dialogo.wav", som)
print(f"build/dialogo.wav  --  {dur:.1f} s, pico {pico:.3f}")
