#!/usr/bin/env python3
"""Grava o audio da derrota: o refrao pausando, a fraseszinha triste (4
notas, uma vez so) e o refrao retomando quando aperta B pra tentar de novo."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from apu import APU, gravar_wav

sym = load_labels("build/jogo-labels.txt")
B, START, RIGHT = 0x02, 0x08, 0x80
FALANTE_TAB = [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1]   # ver test_jogo.py
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
anda(n=20)                            # carrega o minigame (tela de intro)
anda(B, 1)
anda(n=10)                            # troca pra nametable "jogando"

anda(n=90, gravando=True)             # um instante do refrao, antes de errar

nes.bus.ram[sym["player_x"]] = 8      # bem longe -- erra todas as pizzas
for _ in range(3000):
    nes.frame()
    som.extend(apu.quadro(nes.bus.apu))
    if nes.bus.ram[sym["jogo_fase"]] == 2:
        break
anda(n=150, gravando=True)            # a fraseszinha triste inteira (4 notas)

anda(B, 1, gravando=True)             # tenta de novo -- o refrao retoma
anda(n=60, gravando=True)

dur, pico = gravar_wav("build/derrota.wav", som)
print(f"build/derrota.wav  --  {dur:.1f} s, pico {pico:.3f}")
