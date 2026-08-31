#!/usr/bin/env python3
"""Grava o audio da transicao do menu pra pizzaria: o plin, o respiro em
silencio, e o comeco da musica da cena."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from apu import APU, gravar_wav

START = 0x08
nes, apu, som = NES("jogo.nes"), APU(), []

def anda(botao=0, n=1, gravando=False):
    for _ in range(n):
        nes.frame(botao)
        if gravando:
            som.extend(apu.quadro(nes.bus.apu))

anda(n=30, gravando=True)      # um instante de silencio no menu
anda(START, 1, gravando=True)  # o plin
anda(n=90, gravando=True)      # o respiro, depois a cena carrega e a musica comeca

dur, pico = gravar_wav("build/menu-transicao.wav", som)
print(f"build/menu-transicao.wav  --  {dur:.1f} s, pico {pico:.3f}")
